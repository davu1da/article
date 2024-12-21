"use strict";

// Naive browser detection
(function() {
	window.browser = {
		ie: /Trident|MSIE/i.test(navigator.userAgent),
		firefox: /Firefox/i.test(navigator.userAgent)
	};
})();

// XHR helpers
(function() {

	// Get HTML chunks
	window.getChunk = function(uri, callback) {

		// Create XMLHttpRequest object
		var xhr = null;
		if (window.XMLHttpRequest)
			xhr = new window.XMLHttpRequest();
		else if (window.ActiveXObject)
			xhr = new window.ActiveXObject("Microsoft.XMLHTTP");

		// XHR is not available
		if (!xhr)
			return callback(new Error("XHR is not available"), null);

		// Handle error
		xhr.onerror = function() {
			return callback(new Error("Network error"), null);
		};

		// Request aborted
		xhr.onabort = function() {
			return callback(new Error("Request aborted"), null);
		};

		// Successfully loaded
		xhr.onload = function() {

			// Check status code
			if (xhr.status === 200 || xhr.status === 304)
				return callback(null, xhr.responseText);

			// Invalid status code
			return callback(new Error(xhr.statusText), null);
		};

		// Fire the get request
		xhr.open("GET", uri, true);
		xhr.send(null);
	};
})();

// Transition tweening
(function() {

	// Simple requestAnimationFrame polyfill
	var raf = (function() {

		// Fallback to setTimeout @ 60Hz
		var fn = window.requestAnimationFrame;
		if (typeof(fn) != "function") {
			fn = function(callback) {
				setTimeout(callback, 17);
			};
		}

		// Fix skip frames in Firefox Quantum
		if (window.browser.firefox === true) {
			return function(callback) {
				fn(function() {
					fn(callback);
				});
			};
		}

		return fn;
	})();

	// Get computed transition duration
	var duration = function(node) {
		var raw = window.getComputedStyle(node).transitionDuration || "";
		return (parseFloat(raw) || 0) * (raw.indexOf("ms") > 0 ? 1 : 1000);
	};

	// Common pre-process step
	var pre = function(node, type, state, instant) {

		// Unmodified or forced to change immediately
		if (instant === true || node.dataset[type] == state) {
			node.dataset[type] = state;
			return false;
		}

		return true;
	};

	// Common post-process step
	var post = function(node, callback) {

		// Only callback once
		var guard = false;

		// Cancel the pending timer
		clearTimeout(node._transitionTimer);

		// Callback wrapper
		var done = function() {

			// Clear timeout
			clearTimeout(node._transitionTimer);

			// Already fired
			if (guard === true)
				return;

			// Clear the style property after transition
			node.style.cssText = "";

			// Update flag and callback
			guard = true;
			callback();
		};

		// Listen to the transitionend event if available
		node.addEventListener("transitionend", done);

		// Fallback to the plain old setTimeout with a sufficient timeout
		node._transitionTimer = setTimeout(done, duration(node) + 10);
	};

	// Optional callback
	var complete = function(node, callback) {
		if (typeof(callback) == "function")
			callback(node);
	};

	// Fading transition
	var fade = function(state, instant, callback) {

		// Pre-process
		var node = this;
		if (!pre(node, "fade", state, instant))
			return;

		// Ensure the element is rendered as block during the transition
		node.style.display = "block";

		// Update state
		raf(function() {
			node.dataset.fade = state;
			post(node, function() {
				complete(node, callback || instant);
			});
		});
	};

	// Collapsing transition
	var collapse = function(state, instant, callback) {

		// Pre-process
		var node = this;
		if (!pre(node, "collapse", state, instant))
			return;

		// Ensure the element is rendered as block during the transition
		node.style.display = "block";

		// From explicit height to target height
		node.style.maxHeight = state == "collapsed" ? (node.scrollHeight + "px") : "0px";
		raf(function() {
			node.style.maxHeight = state == "collapsed" ? "0px" : (node.scrollHeight + "px");
			node.dataset.collapse = state;
			post(node, function() {
				complete(node, callback || instant);
			});
		});
	};

	// Height clipping
	var clip = function(state, instant, callback) {

		// Pre-process
		var node = this;
		if (!pre(node, "clip", state, instant))
			return;

		// Get current height
		var prev = node.dataset.clip;
		var from = node.scrollHeight + "px";

		// Get target height
		node.dataset.clip = state;
		var to = node.scrollHeight + "px";

		// Show all inner elements during the transition
		node.dataset.clip = "false";
		node.style.maxHeight = from;
		raf(function() {
			node.style.maxHeight = to;
			post(node, function() {
				node.dataset.clip = state;
				complete(node, callback || instant);
			});
		});

	};

	// Export the binding function
	window.tween = function(node) {
		node.fade = fade.bind(node);
		node.collapse = collapse.bind(node);
		node.clip = clip.bind(node);
		return node;
	};
})();

// 搜索栏相关的UI事件处理
(function() {

    // 选择DOM元素
    var wrapper = document.getElementById("search-wrapper");  // 获取搜索栏外层容器
    var input = document.getElementById("search-input");      // 获取搜索输入框
    var clear = document.getElementById("search-clear");      // 获取清除按钮
	var type = document.getElementById("search-type");    // 获取搜索类型选择框
    // 定义回调函数
	var originalLayout = document.body.dataset.layout;
    /**
     * 当搜索输入框内容变化或点击时触发结果布局显示
     */
    var triggerResultLayout = function() {
        if (document.body.dataset.layout != "result")
            document.body.dataset.layout = "result";  // 如果当前布局不是结果页，则切换为结果页布局
    };

    /**
     * 当搜索栏获得焦点时更新其样式
     */
    var focusSearchBar = function() {
        wrapper.dataset.focus = "true";  // 设置搜索栏外层容器的data-focus属性为true，表示已聚焦
    };

    /**
     * 当搜索栏失去焦点时更新其样式
     */
    var blurSearchBar = function() {
        wrapper.dataset.focus = "false";  // 设置搜索栏外层容器的data-focus属性为false，表示失去焦点
    };

    /**
     * 清除输入框内容并阻止默认行为
     */
    var clearInputBox = function(event) {
        event.preventDefault();  // 阻止默认行为（如表单提交）
        input.value = "";        // 清空输入框内容
    };

	var clearSearchType = function(event) {
		type.value = "";
	};
    /**
     * 清除浏览器前进后退缓存中的输入框原始值
     */
    var clearBackForwardCache = function(event) {
        if (event.persisted && input.dataset.original)
            input.value = input.dataset.original;  // 如果页面是从缓存中恢复且存在原始值，则恢复输入框的原始值
    };

    // 绑定事件监听器
    input.addEventListener("input", triggerResultLayout);  // 输入框内容变化时触发结果布局显示
    input.addEventListener("click", triggerResultLayout);  // 点击输入框时触发结果布局显示
    input.addEventListener("focus", focusSearchBar);       // 输入框获得焦点时更新样式
    input.addEventListener("blur", blurSearchBar);         // 输入框失去焦点时更新样式
    clear.addEventListener("click", clearInputBox);       // 点击清除按钮时清空输入框
    clear.addEventListener("mousedown", clearInputBox);   // 按下清除按钮时清空输入框
    window.addEventListener("pageshow", clearBackForwardCache);  // 页面显示时清除缓存中的输入框原始值

    // 自动聚焦到输入框（仅当页面初始布局为首页且非IE浏览器时）
    if (document.body.dataset.layout == "home" && !window.browser.ie)
        input.focus();  // 自动将焦点设置到输入框

	document.addEventListener("click", function(event) {
        if (event.target != type && event.target !== input && !input.contains(event.target)) {
            document.body.dataset.layout = originalLayout;  // 点击输入框外的地方时恢复原来的布局
        }
    });
})();

// Censorship
(function() {

	// Censor class
	var Censor = function(profiles) {
		this.enabled = profiles.length > 0;
		this.profiles = Object.create(null);
		for (var i = 0; i < profiles.length; i++)
			this.profiles[profiles[i].name] = profiles[i];
	};

	Censor.prototype._createWarning = function() {

		// Already created
		if (document.getElementById("censored"))
			return false;

		// Create element
		var warn = document.createElement("div");
		warn.setAttribute("id", "censored");
		warn.classList.add("tips");
		warn.textContent = i18n.censorWarning;

		// Prepend to the result container
		var parent = document.querySelector("main");
		parent.insertBefore(warn, parent.firstChild);

		return true;
	};

	Censor.prototype._remove = function(node, depth) {

		// Invalid node
		var parent = node.parentNode;
		if (!node || !parent)
			return false;

		// Remove recursively
		node.parentNode.removeChild(node);
		if (depth > 0)
			return this._remove(parent, depth - 1);

		return true;
	};

	Censor.prototype._testAgainst = function(text, regexes) {
		for (var i = 0; i < regexes.length; i++)
			if (regexes[i].test(text))
				return true;
		return false;
	};

	Censor.prototype._getText = function(node, selector, attr) {

		// Get text from attribute
		if (typeof(attr) == "string")
			return node.getAttribute(attr);

		// Get text from child selector
		var contents = node.querySelectorAll(selstyles/dark.cssector);
		var texts = [];
		for (var i = 0; i < contents.length; i++)
			texts.push(contents[i].textContent);

		return texts.join(" ");
	};

	Censor.prototype.filter = function(name, dry) {

		// Check availability
		if (!this.enabled || !this.profiles[name])
			return false;

		// Select candidate nodes
		var profile = this.profiles[name];
		var candidates = document.querySelectorAll(profile.nodeSelector);
		if (candidates.length === 0)
			return false;

		// Check each node
		var hit = false;
		for (var i = 0; i < candidates.length; i++) {
			var candidate = candidates[i];

			// Test regexes
			var text = this._getText(candidate, profile.contentSelector, profile.contentAttribute);
			if (!this._testAgainst(text, profile.regexes))
				continue;

			// We got a hit!
			hit = true;

			// Dry run
			if (dry === true)
				return true;

			// Remove by selector
			if (typeof(profile.removeSelector) == "string") {
				var removes = document.querySelectorAll(profile.removeSelector);
				for (var j = 0; j < removes.length; j++)
					this._remove(removes[j], 0);
			}

			// Remove self and parents
			if (typeof(profile.removeParents) == "number")
				this._remove(candidate, profile.removeParents);
		}

		// Jobs done
		if (!hit || dry === true)
			return hit;

		// Optional warning label
		if (profile.warning === true)
			this._createWarning();

		// Optional cleanup
		if (typeof(profile.cleanup) == "function")
			profile.cleanup();

		return hit;
	};

	// Simple cipher
	var cipher = function(x) {
		var r = [];
		var c = [];
		if (typeof(x) != "string" || x.length === 0)
			return r;
		x = window.atob(x).split("-");
		for (var i = 0; i < x.length; i++)
			c.push(String.fromCharCode(parseInt(x[i], 16)));
		c = c.join("").split("\n");
		for (var i = 0; i < c.length; i++)
			r.push(new RegExp(c[i], "i"));
		return r;
	};

	// Filter profiles
	var profiles = [];
	var l1 = cipher(window.i18n.censorLevel1);
	var l2 = cipher(window.i18n.censorLevel2).concat(l1);
	if (l1.length > 0) {
		profiles.push({
			name: "query",
			nodeSelector: "#search-input",
			contentAttribute: "data-original",
			removeSelector: "main>*",
			warning: true,
			regexes: l1
		});
		profiles.push({
			name: "web",
			nodeSelector: ".card[data-type=web]",
			contentSelector: "h3,p",
			removeParents: 0,
			warning: true,
			regexes: l1
		});
	}
	if (l2.length > 0) {
		profiles.push({
			name: "showcase",
			nodeSelector: "#showcase li",
			contentSelector: "h5,div>a",
			removeParents: 0,
			warning: false,
			regexes: l2
		});
		profiles.push({
			name: "card",
			nodeSelector: ".card[data-type=fact]",
			contentSelector: "header>div>h2,header>div>span",
			removeParents: 0,
			warning: true,
			regexes: l2
		});
		profiles.push({
			name: "fact",
			nodeSelector: ".fact",
			contentSelector: "dd",
			removeParents: 1,
			warning: true,
			regexes: l2,
			cleanup: function() {

				// Remove empty fact sections
				var sections = document.querySelectorAll(".card[data-type=fact]>div>section");
				for (var i = 0; i < sections.length; i++)
					if (sections[i].children[1].children.length === 0)
						sections[i].parentNode.removeChild(sections[i]);

				// Remove empty fact cards
				var cards = document.querySelectorAll(".card[data-type=fact]");
				for (var i = 0; i < cards.length; i++)
					if (cards[i].children[1].children.length === 0)
						cards[i].parentNode.removeChild(cards[i]);
			}
		});
	}

	// Create censor instance
	window.censor = new Censor(profiles);
	if (window.localStorage && window.localStorage.getItem("konami") == "30")
		window.censor.enabled = false;

	// First run
	window.censor.filter("query");
	window.censor.filter("card");
	window.censor.filter("fact");
	window.censor.filter("web");
})();

// Next page
(function() {

	// Select the next page button
	var getNextPageButton = function() {
		return document.querySelector(".card[data-type=next]");
	};

	// Load and render the next page
	var loadNextPage = function() {

		// Check the existence of the button
		var button = getNextPageButton();
		if (!button) return;

		// Enter loading state
		loadingNextPageButton();

		// Build the request URI
		var uri = "/search?ajax=1";
		uri += "&offset=" + button.dataset.offset;
		uri += "&size=" + button.dataset.size;
		uri += "&q=" + encodeURIComponent(button.dataset.input);

		// Get the next page
		window.getChunk(uri, function(err, content) {

			// Network error
			if (err) {
				resetNextPageButton();
				return console.error(err);
			}

			// Remove the stale button and append the new fragment
			var fragment = document.createRange().createContextualFragment(content);
			button.parentNode.replaceChild(fragment, button);

			// Censor new results
			if (window.censor)
				window.censor.filter("web");

			// Initialize the new button
			resetNextPageButton();
		});
	};

	// Reinitialize the next page button
	var resetNextPageButton = function() {

		// Check the existence of the button
		var button = getNextPageButton();
		if (!button) return;

		// Bind event listener and reset state
		button.addEventListener("click", loadNextPage);
		button.dataset.loading = "false";
		button.textContent = i18n.nextPageLoad;
	};

	// Enter the loading state
	var loadingNextPageButton = function() {

		// Check the existence of the button
		var button = getNextPageButton();
		if (!button) return;

		// Remove event listener and reset state
		button.removeEventListener("click", loadNextPage);
		button.dataset.loading = "true";
		button.textContent = i18n.nextPageLoading;
	};

	// Initialize the button
	resetNextPageButton();
})();

// Fact search result collapsing
(function() {

	// Layout constants
	var mobile = window.screen.width <= 760;
	var k_EXPANDED_CARDS = mobile ? 2 : 2;
	var k_EXPANDED_FACTS_MIXED = mobile ? 15 : 20;
	var k_EXPANDED_FACTS_DESCRIPTION = mobile ? 4 : 6;
	var k_EXPANDED_FACTS_PROPERTY = mobile ? 6 : 10;
	var k_EXPANDED_FACTS_TAG = mobile ? 10 : 15;
	var k_EXPANDED_FACTS_SYNONYM = mobile ? 4 : 6;

	// Initialize card elements
	var initCard = function(card, index) {

		// Initialize sections
		var sections = card.querySelectorAll("section[data-scope]");
		for (var i = 0; i < sections.length; i++)
			initSection(sections[i], card, index);

		// Interactive elements
		var header = card.children[0];
		var content = card.children[1];
		var hint = header.getElementsByTagName("a")[0];

		// Bind transitions
		window.tween(content);
		window.tween(hint);

		// Folding state
		var expanded = true;
		if (index >= k_EXPANDED_CARDS)
			expanded = false;
		if (index > 0 && mobile && card.getBoundingClientRect().bottom >= window.innerHeight)
			expanded = false;
		if (index > 0 && !mobile && card.getBoundingClientRect().top >= window.innerHeight)
			expanded = false;
		if (index > 0 && card.dataset.subtype == "value")
			expanded = false;

		// Fold cards
		card.dataset.folded = expanded ? "false" : "true";
		content.collapse(expanded ? "expanded" : "collapsed", true);
		hint.fade(expanded ? "hidden" : "visible", true);

		// Handle clicks
		header.addEventListener("click", function() {
			if (card.dataset.folded == "true") {
				card.dataset.folded = "false";
				content.collapse("expanded");
				hint.fade("hidden");
			} else {
				card.dataset.folded = "true";
				content.collapse("collapsed");
				hint.fade("visible");
			}
		});
	};

	// Initialize section elements
	var initSection = function(section, card, index) {

		// Initialize facts
		var facts = section.querySelectorAll(".fact");
		for (var i = 0; i < facts.length; i++)
			initFact(facts[i], section, card, index);

		// Truncate long sections
		var content = section.getElementsByTagName("div")[0];
		var cells = content.children;
		var limit = k_EXPANDED_FACTS_MIXED;
		switch (section.dataset.scope) {
			case "description":
				limit = k_EXPANDED_FACTS_DESCRIPTION;
				break;
			case "property":
				limit = k_EXPANDED_FACTS_PROPERTY;
				break;
			case "tag":
				limit = k_EXPANDED_FACTS_TAG;
				break;
			case "synonym":
				limit = k_EXPANDED_FACTS_SYNONYM;
				break;
		}
		if (cells.length <= limit)
			return;

		// Hide extra cells
		section.dataset.truncate = "peek";
		for (var i = limit; i < cells.length; i++)
			cells[i].dataset.extra = "true";

		// Bind transitions
		window.tween(content).clip("true", true);

		// Handle clicks
		var footer = section.lastElementChild;
		footer.addEventListener("click", function() {
			if (section.dataset.truncate == "peek") {
				section.dataset.truncate = "all";
				content.clip("false");
			} else {
				section.dataset.truncate = "peek";
				content.clip("true");
			}
		});
	};

	// Initialize fact elements
	var initFact = function(fact, section, card, index) {

		// Interactive elements
		var header = fact.children[0];
		var contexts = fact.children[1];
		var cell = fact.parentNode;

		// Bind transitions
		window.tween(contexts);

		// Determine initial layout
		if (card.dataset.subtype == "value") {
			contexts.collapse("expanded", true);
			cell.dataset.span = "row";
			fact.dataset.render = "tuple";
		} else {
			contexts.collapse("collapsed", true);
			cell.dataset.span = "cell";
			fact.dataset.render = "cell";
		}

		// Handle clicks
		header.addEventListener("click", function() {
			if (contexts.dataset.collapse == "collapsed") {
				cell.dataset.span = "row";
				fact.dataset.render = "tuple";
				contexts.collapse("expanded");
			} else {
				contexts.collapse("collapsed", function() {
					cell.dataset.span = "cell";
					fact.dataset.render = "cell";
				});
			}
		});
	};

	// Get all fact cards
	var cards = document.querySelectorAll(".card[data-type=fact]");
	for (var i = 0; i < cards.length; i++)
		initCard(cards[i], i);
})();

// Showcase carousel
(function() {

	// Carousel loop
	var offset = 0;
	var next = function() {

		// Break if we're no longer in the home layout
		if (document.body.dataset.layout != "home")
			return;

		// Select the next record by offset
		var wrapper = document.getElementById("showcase");
		var list = wrapper.getElementsByTagName("ul")[0];
		var record = list.children[(offset++) % list.children.length];

		// Fade in and out
		record.fade("visible", function() {
			setTimeout(function() {
				record.fade("hidden", function() {
					setTimeout(next, 1000);
				});
			}, 9000);
		});
	};

	// Fetch and inject showcases
	var inject = function() {

		// Break if we're no longer in the home layout
		if (document.body.dataset.layout != "home")
			return;

		// Fetch showcase chunks
		window.getChunk("/showcase", function(err, content) {

			// Failed to get chunks
			if (err)
				return console.error(err);

			// Inject fragment to the home section
			var fragment = document.createRange().createContextualFragment(content);
			document.getElementById("home").appendChild(fragment);

			// Censor showcases
			if (window.censor)
				window.censor.filter("showcase");

			// The fragment might be empty
			var wrapper = document.getElementById("showcase");
			var list = wrapper.getElementsByTagName("ul")[0];
			if (list.children.length === 0)
				return;

			// Sort randomly leveraging appendChild's auto removal
			for (var i = list.children.length; i >= 0; i--)
				list.appendChild(list.children[(Math.random() * i) | 0]);

			// Bind transitions and initialize states
			for (var i = 0; i < list.children.length; i++)
				window.tween(list.children[i]).fade("hidden", true);

			// Start the carousel
			setTimeout(next, 2000);
		});
	};

	// Initial delay after loaded
	if (document.body.dataset.layout == "home")
		setTimeout(inject, 4000);
})();




// Submit 





// Search suggestions
(function() {

	// 选择DOM元素
	var input = document.getElementById("search-input"); // 获取搜索输入框元素
	var dropdown = document.getElementById("search-suggestions"); // 获取建议下拉列表元素
	var form = document.getElementById("search-form"); // 获取搜索表单元素
	// var type = document.getElementById("search-type");


	// 创建缓存对象用于存储建议查询结果
	var cache = Object.create(null);
	var retrieveSuggestions = function(text, size, callback) { // 定义获取建议的方法

		// 拼接查询URL，并使用其作为缓存键
		var uri = "/suggest?size=" + size + "&q=" + encodeURIComponent(text);

		// 如果缓存中有数据，则直接调用回调函数返回缓存的数据
		if (cache[uri])
			return callback(null, cache[uri], true);

		// 否则从服务器获取数据
		window.getChunk(uri, function(err, data) {

			// 解析数据并更新缓存，然后调用回调函数
			return callback(err, data ? (cache[uri] = JSON.parse(data)) : null, false);
		});
	};

	// 渲染建议卡片
	var renderSuggestionCard = function(text, before, minimum) { // 定义渲染建议卡片的方法

		// 忽略空查询文本
		if (text.trim().length === 0)
			return;

		// 获取顶部建议
		retrieveSuggestions(text, 9, function(err, suggestions, fromCache) {

			// 如果有错误或建议数量不足最小值，则不渲染卡片
			if (err || !suggestions || suggestions.length < minimum)
				return;

			// 创建建议卡片div元素
			var div = document.createElement("div");
			div.setAttribute("class", "card");
			div.dataset.type = "suggest";

			// 创建建议网格ul元素
			var ul = document.createElement("ul");
			ul.setAttribute("class", "queue-in");

			// 渲染链接li元素
			suggestions.forEach(function(content) {
				var li = document.createElement("li");
				var a = document.createElement("a");
				a.textContent = content;
				a.dataset.decoration = "search";
				a.setAttribute("href", "/search?q=" + encodeURIComponent(content));
				a.setAttribute("target", "_self");
				li.appendChild(a);
				ul.appendChild(li);
			});

			// 将ul插入到div中，并将div插入到指定位置之前
			div.appendChild(ul);
			document.querySelector("main").insertBefore(div, before || null);
		});
	};

	// 下拉菜单状态标志
	var selected = 0;
	var original = "";

	// 清除下拉菜单
	var clearDropdown = function() {
		selected = -1;
		while (dropdown.lastChild)
			dropdown.removeChild(dropdown.lastChild);
	};

	// 重置活动建议项
	var resetActiveItem = function() {
		for (var i = 0, l = dropdown.children.length; i < l; i++)
			dropdown.children[i].dataset.active = i === selected ? "true" : "false";
	};

	// 获取建议项索引
	var indexInDropdown = function(li) {
		for (var i = 0, l = dropdown.children.length; i < l; i++)
			if (dropdown.children[i] === li)
				return i;
		return -1;
	};

	// 鼠标进入建议项时触发
	var enterDropdownItem = function() {
		selected = indexInDropdown(this);
		resetActiveItem();
	};

	// 鼠标离开活动项时触发
	var leaveDropdownItem = function() {
		if (selected === indexInDropdown(this)) {
			selected = -1;
			resetActiveItem();
		}
	};

	// 点击建议项时触发
	var clickDropdownItem = function() {
		input.value = this.textContent;
		// form.action = "/test";
		form.submit();
	};

	// 更新搜索下拉菜单
	var latest = 0;
	var updateDropdown = function(text) {

		// 从搜索栏获取文本
		if (typeof(text) != "string") {
			var q = input.value;
			text = q.trim();

			// 保留尾随空格
			if (text.length > 0 && q[q.length - 1] == " ")
				text += " ";
		}

		// 如果字符串为空则清除下拉菜单
		if (text.length === 0)
			return clearDropdown();

		// 获取顶部建议
		var id = ++latest % 0xFFFF;
		retrieveSuggestions(text, 8, function(err, suggestions, fromCache) {

			// 如果有错误或请求ID已过期则返回
			if (err || id !== latest)
				return;

			// 构建下拉菜单
			var fragment = document.createDocumentFragment();
			suggestions.forEach(function(content) {
				var li = document.createElement("li");
				li.textContent = content;
				li.addEventListener("mouseenter", enterDropdownItem);
				li.addEventListener("mouseleave", leaveDropdownItem);
				li.addEventListener("mousedown", clickDropdownItem);
				fragment.appendChild(li);
			});

			clearDropdown();
			dropdown.appendChild(fragment);
		});
	};

	// 在输入框输入时更新下拉菜单
	var timeout = null;
	input.addEventListener("input", function() {
		original = input.value;
		clearTimeout(timeout);
		timeout = setTimeout(updateDropdown, 200);
	});

	// 当输入框获得焦点时更新下拉菜单
	input.addEventListener("focus", function() {
		original = input.value;
		clearDropdown();
		updateDropdown();
	});

	// 处理箭头键和Tab键
	input.addEventListener("keydown", function(event) {

		// 如果下拉菜单为空则不做任何操作
		var total = dropdown.children.length;
		if (total === 0)
			return;

		// 根据按键代码处理不同情况
		switch (event.keyCode) {
			case 9: // Tab键
				event.preventDefault();
				if (total > 0) {
					original = input.value = dropdown.children[selected >= 0 ? selected : 0].textContent;
					updateDropdown();
				}
				break;
			case 38: // 上箭头键
				event.preventDefault();
				selected = selected < 0 ? total - 1 : selected - 1;
				input.value = selected < 0 ? original : dropdown.children[selected].textContent;
				resetActiveItem();
				break;
			case 40: // 下箭头键
				event.preventDefault();
				selected = selected + 1 >= total ? -1 : selected + 1;
				input.value = selected < 0 ? original : dropdown.children[selected].textContent;
				resetActiveItem();
				break;
		}
	});

	// 渲染建议卡片
	if (input.dataset.original && (!window.censor || !window.censor.filter("query", true))) {
		var button = document.querySelector("div.card[data-type=next]");
		renderSuggestionCard(input.dataset.original, button, button ? 6 : 1);
	}
})();

// Bibliography
// (function() {

// 	// 选择DOM元素
// 	var input = document.getElementById("search-input"); // 获取搜索输入框元素
// 	var dropdown = document.getElementById("search-suggestions"); // 获取建议下拉列表元素
// 	var form = document.getElementById("search-form"); // 获取搜索表单元素

// 	// 创建缓存对象用于存储建议查询结果
// 	var cache = Object.create(null);
// 	var retrieveSuggestions = function(text, size, callback) { // 定义获取建议的方法

// 		// 拼接查询URL，并使用其作为缓存键
// 		var uri = "/suggest?size=" + size + "&q=" + encodeURIComponent(text);

// 		// 如果缓存中有数据，则直接调用回调函数返回缓存的数据
// 		if (cache[uri])
// 			return callback(null, cache[uri], true);

// 		// 否则从服务器获取数据
// 		window.getChunk(uri, function(err, data) {

// 			// 解析数据并更新缓存，然后调用回调函数
// 			return callback(err, data ? (cache[uri] = JSON.parse(data)) : null, false);
// 		});
// 	};

// 	// 渲染建议卡片
// 	var renderSuggestionCard = function(text, before, minimum) { // 定义渲染建议卡片的方法

// 		// 忽略空查询文本
// 		if (text.trim().length === 0)
// 			return;

// 		// 获取顶部建议
// 		retrieveSuggestions(text, 9, function(err, suggestions, fromCache) {

// 			// 如果有错误或建议数量不足最小值，则不渲染卡片
// 			if (err || !suggestions || suggestions.length < minimum)
// 				return;

// 			// 创建建议卡片div元素
// 			var div = document.createElement("div");
// 			div.setAttribute("class", "card");
// 			div.dataset.type = "suggest";

// 			// 创建建议网格ul元素
// 			var ul = document.createElement("ul");
// 			ul.setAttribute("class", "queue-in");

// 			// 渲染链接li元素
// 			suggestions.forEach(function(content) {
// 				var li = document.createElement("li");
// 				var a = document.createElement("a");
// 				a.textContent = content;
// 				a.dataset.decoration = "search";
// 				a.setAttribute("href", "/search?q=" + encodeURIComponent(content));
// 				a.setAttribute("target", "_self");
// 				li.appendChild(a);
// 				ul.appendChild(li);
// 			});

// 			// 将ul插入到div中，并将div插入到指定位置之前
// 			div.appendChild(ul);
// 			document.querySelector("main").insertBefore(div, before || null);
// 		});
// 	};

// 	// 下拉菜单状态标志
// 	var selected = 0;
// 	var original = "";

// 	// 清除下拉菜单
// 	var clearDropdown = function() {
// 		selected = -1;
// 		while (dropdown.lastChild)
// 			dropdown.removeChild(dropdown.lastChild);
// 	};

// 	// 重置活动建议项
// 	var resetActiveItem = function() {
// 		for (var i = 0, l = dropdown.children.length; i < l; i++)
// 			dropdown.children[i].dataset.active = i === selected ? "true" : "false";
// 	};

// 	// 获取建议项索引
// 	var indexInDropdown = function(li) {
// 		for (var i = 0, l = dropdown.children.length; i < l; i++)
// 			if (dropdown.children[i] === li)
// 				return i;
// 		return -1;
// 	};

// 	// 鼠标进入建议项时触发
// 	var enterDropdownItem = function() {
// 		selected = indexInDropdown(this);
// 		resetActiveItem();
// 	};

// 	// 鼠标离开活动项时触发
// 	var leaveDropdownItem = function() {
// 		if (selected === indexInDropdown(this)) {
// 			selected = -1;
// 			resetActiveItem();
// 		}
// 	};

// 	// 点击建议项时触发
// 	var clickDropdownItem = function() {
// 		input.value = this.textContent;
// 		form.submit();
// 	};

// 	// 更新搜索下拉菜单
// 	var latest = 0;
// 	var updateDropdown = function(text) {

// 		// 从搜索栏获取文本
// 		if (typeof(text) != "string") {
// 			var q = input.value;
// 			text = q.trim();

// 			// 保留尾随空格
// 			if (text.length > 0 && q[q.length - 1] == " ")
// 				text += " ";
// 		}

// 		// 如果字符串为空则清除下拉菜单
// 		if (text.length === 0)
// 			return clearDropdown();

// 		// 获取顶部建议
// 		var id = ++latest % 0xFFFF;
// 		retrieveSuggestions(text, 8, function(err, suggestions, fromCache) {

// 			// 如果有错误或请求ID已过期则返回
// 			if (err || id !== latest)
// 				return;

// 			// 构建下拉菜单
// 			var fragment = document.createDocumentFragment();
// 			suggestions.forEach(function(content) {
// 				var li = document.createElement("li");
// 				li.textContent = content;
// 				li.addEventListener("mouseenter", enterDropdownItem);
// 				li.addEventListener("mouseleave", leaveDropdownItem);
// 				li.addEventListener("mousedown", clickDropdownItem);
// 				fragment.appendChild(li);
// 			});

// 			clearDropdown();
// 			dropdown.appendChild(fragment);
// 		});
// 	};

// 	// 在输入框输入时更新下拉菜单
// 	var timeout = null;
// 	input.addEventListener("input", function() {
// 		original = input.value;
// 		clearTimeout(timeout);
// 		timeout = setTimeout(updateDropdown, 200);
// 	});

// 	// 当输入框获得焦点时更新下拉菜单
// 	input.addEventListener("focus", function() {
// 		original = input.value;
// 		clearDropdown();
// 		updateDropdown();
// 	});

// 	// 处理箭头键和Tab键
// 	input.addEventListener("keydown", function(event) {

// 		// 如果下拉菜单为空则不做任何操作
// 		var total = dropdown.children.length;
// 		if (total === 0)
// 			return;

// 		// 根据按键代码处理不同情况
// 		switch (event.keyCode) {
// 			case 9: // Tab键
// 				event.preventDefault();
// 				if (total > 0) {
// 					original = input.value = dropdown.children[selected >= 0 ? selected : 0].textContent;
// 					updateDropdown();
// 				}
// 				break;
// 			case 38: // 上箭头键
// 				event.preventDefault();
// 				selected = selected < 0 ? total - 1 : selected - 1;
// 				input.value = selected < 0 ? original : dropdown.children[selected].textContent;
// 				resetActiveItem();
// 				break;
// 			case 40: // 下箭头键
// 				event.preventDefault();
// 				selected = selected + 1 >= total ? -1 : selected + 1;
// 				input.value = selected < 0 ? original : dropdown.children[selected].textContent;
// 				resetActiveItem();
// 				break;
// 		}
// 	});

// 	// 渲染建议卡片
// 	if (input.dataset.original && (!window.censor || !window.censor.filter("query", true))) {
// 		var button = document.querySelector("div.card[data-type=next]");
// 		renderSuggestionCard(input.dataset.original, button, button ? 6 : 1);
// 	}
// })();

// Ready player one
(function() {

	// Check support of local storage and typed array
	// We use a fixed length Uint8Array as the key buffer
	if (!window.localStorage || !window.ArrayBuffer)
		return;

	// Ring buffer for key strokes
	var ring = new Uint8Array(10);
	var ptr = -1;
	var store = window.localStorage;

	// Reversed DJB2 hashing for a given size
	var rewind = function(size) {
		var h = 5381;
		for (var i = 0, l = ring.length; i < size; i++)
			h = (h * 33) ^ ring[(ptr - i + l) % l];
		return h >>> 0;
	};

	// Listen for strokes
	window.addEventListener("keydown", function(event) {
		ring[ptr = (ptr + 1) % ring.length] = event.keyCode;

		// For debugging only, do the right things and do things right, cheers!
		if (event.keyCode === 0x41 && rewind(10) === 0x6b040f26) {
			store.setItem("konami", store.getItem("konami") == "30" ? "0" : "30");
			window.location.reload(false);
		}
	});
})();

// Embedded arguments
(function() {
	var args = window.args = Object.create(null);
	var hash = window.location.hash.substr(1);
	var kvs = hash.split(";");
	for (var i = 0; i < kvs.length; i++) {
		var kv = kvs[i].split("=");
		switch (kv[0].trim()) {
			case "theme":
				args.theme = (kv[1] || "").trim();
				break;
		}
	}
})();

// Theme Switcher
// (function() {
// 	// 使用从HTML中获取的路径
// 	// 定义DARK_STYLE变量，值为从window.THEME_PATHS对象中获取的DARK_STYLE路径
// 	var DARK_STYLE = window.THEME_PATHS.DARK_STYLE;
// 	// 定义LIGHT_STYLE变量，值为从window.THEME_PATHS对象中获取的LIGHT_STYLE路径
// 	var LIGHT_STYLE = window.THEME_PATHS.LIGHT_STYLE;
// 	// 获取ID为"theme-toggler"的元素，通常是一个切换按钮
// 	var toggler = document.getElementById("theme-toggler");
// 	// 获取文档的<head>元素，用于插入样式表链接
// 	var head = document.getElementsByTagName("head")[0];
// 	// 创建一个新的<link>元素，用于加载CSS样式表
// 	var link = document.createElement("link");
// 	// 设置<link>元素的ID为"theme-style"
// 	link.id = "theme-style";
// 	// 设置<link>元素的rel属性为"stylesheet"，表示这是一个样式表链接
// 	link.rel = "stylesheet";
// 	// 根据URL参数或localStorage中的主题设置，决定初始加载的样式表
// 	if ((window.args && window.args.theme == "light") || window.localStorage.getItem("magi-theme") == "light") {
// 		// 如果主题参数为"light"或localStorage中存储的主题为"light"
// 		// 设置切换按钮为选中状态
// 		toggler.checked = true;
// 		// 设置<link>元素的href属性为LIGHT_STYLE路径
// 		link.href = LIGHT_STYLE;
// 	} else {
// 		// 否则，设置切换按钮为未选中状态
// 		toggler.checked = false;
// 		// 设置<link>元素的href属性为DARK_STYLE路径
// 		link.href = DARK_STYLE;
// 	}
// 	// 将<link>元素添加到<head>中，加载相应的样式表

// 	head.appendChild(link);

// 	// 为切换按钮添加点击事件监听器
// 	toggler.addEventListener("click", function() {
// 		// 获取ID为"theme-style"的<link>元素
// 		var link = document.getElementById("theme-style");
// 		// 获取当前<link>元素的href属性值
// 		var href = link.getAttribute("href");
// 		// 根据当前加载的样式表路径，切换到另一种主题
// 		if (href == DARK_STYLE) {
// 			// 如果当前加载的是暗色主题
// 			// 设置<link>元素的href属性为LIGHT_STYLE路径，切换到亮色主题
// 			link.setAttribute("href", LIGHT_STYLE);
// 			// 设置切换按钮为选中状态
// 			toggler.checked = true;
// 			// 将当前主题存储到localStorage中
// 			window.localStorage.setItem("magi-theme", "light");
// 		} else {
// 			// 否则，当前加载的是亮色主题
// 			// 设置<link>元素的href属性为DARK_STYLE路径，切换到暗色主题
// 			link.setAttribute("href", DARK_STYLE);
// 			// 设置切换按钮为未选中状态
// 			toggler.checked = false;
// 			// 将当前主题存储到localStorage中
// 			window.localStorage.setItem("magi-theme", "dark");
// 		}
// 		// 刷新页面以应用新的主题
//         location.reload();
// 	});
// })();
(function() {
    var DARK_STYLE = window.THEME_PATHS.DARK_STYLE;
    var LIGHT_STYLE = window.THEME_PATHS.LIGHT_STYLE;
    var toggler = document.getElementById("theme-toggler");
    var head = document.getElementsByTagName("head")[0];
    var link = document.createElement("link");

    link.id = "theme-style";
    link.rel = "stylesheet";

    // 初始设置
    if ((window.args && window.args.theme == "light") || window.localStorage.getItem("magi-theme") == "light") {
        toggler.checked = true;
        link.href = LIGHT_STYLE;
    } else {
        toggler.checked = false;
        link.href = DARK_STYLE;
    }
    head.appendChild(link);

    // 切换主题事件监听器
    toggler.addEventListener("click", function() {
        var link = document.getElementById("theme-style");
        var href = link.getAttribute("href");

        if (href === DARK_STYLE) {
            link.setAttribute("href", LIGHT_STYLE);
            toggler.checked = true;
            window.localStorage.setItem("magi-theme", "light");
        } else {
            link.setAttribute("href", DARK_STYLE);
            toggler.checked = false;
            window.localStorage.setItem("magi-theme", "dark");
        }

        // 强制重新计算样式以确保立即生效
        setTimeout(() => {
            document.body.style.cssText = ''; // 清除任何临时样式
        }, 0);
		// location.reload();
    });
})();