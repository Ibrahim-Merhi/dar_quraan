(() => {
	const initialiseGuide = () => {
		const root = document.querySelector(".from-markdown");
		const navigation = root?.querySelector(".dq-quick-nav");

		if (!root || !navigation) {
			return;
		}

		const activeLanguage = window.frappe?.boot?.lang || document.documentElement.lang || "";
		const isArabicGuide =
			activeLanguage.toLowerCase().startsWith("ar") ||
			window.getComputedStyle(root).direction === "rtl";

		if (isArabicGuide) {
			root.querySelectorAll(".dq-guide-shot img").forEach((image) => {
				image.src = image.src.replace(/\.png(?=\?|$)/, "-ar.png");
			});

			root.querySelectorAll(".dq-guide-shot a").forEach((link) => {
				link.href = link.href.replace(/\.png(?=\?|$)/, "-ar.png");
			});
		}

		const nodes = Array.from(root.children);
		const sections = new Map();
		let currentSection = null;

		nodes.forEach((node) => {
			if (node.tagName === "H2") {
				currentSection = document.createElement("section");
				currentSection.className = "dq-guide-section";
				currentSection.dataset.sectionId = node.id;
				node.dataset.originalTitle = node.textContent.replace(/^\d+\.\s*/, "");
				root.insertBefore(currentSection, node);
				sections.set(node.id, currentSection);
			}

			if (currentSection && node !== currentSection) {
				currentSection.appendChild(node);
			}
		});

		sections.forEach((section) => {
			section.querySelectorAll("h3").forEach((heading) => {
				heading.dataset.originalTitle = heading.textContent.replace(
					/^\d+(?:\.\d+)*\.?\s*/,
					""
				);
			});
		});

		const links = Array.from(navigation.querySelectorAll("a[data-sections]"));
		const emptyState = root.querySelector(".dq-guide-empty");

		const showSelection = (link, updateHistory = true) => {
			const selectedIds = (link.dataset.sections || "")
				.split(",")
				.map((id) => id.trim())
				.filter(Boolean);

			sections.forEach((section, id) => {
				section.hidden = !selectedIds.includes(id);
			});

			selectedIds.forEach((id, sectionIndex) => {
				const section = sections.get(id);

				if (!section) {
					return;
				}

				const heading = section.querySelector(":scope > h2");
				const sectionNumber = String(sectionIndex + 1);
				heading.textContent = [sectionNumber, heading.dataset.originalTitle].join(". ");

				section.querySelectorAll("h3").forEach((subheading, subIndex) => {
					subheading.textContent = `${sectionNumber}.${subIndex + 1} ${
						subheading.dataset.originalTitle
					}`;
				});
			});

			links.forEach((item) => {
				const active = item === link;
				item.classList.toggle("is-active", active);
				item.setAttribute("aria-selected", String(active));
			});

			if (emptyState) {
				emptyState.hidden = true;
			}

			if (updateHistory) {
				history.replaceState(null, "", link.getAttribute("href"));
			}
		};

		sections.forEach((section) => {
			section.hidden = true;
		});

		links.forEach((link) => {
			link.setAttribute("role", "tab");
			link.setAttribute("aria-selected", "false");
			link.addEventListener("click", (event) => {
				event.preventDefault();
				showSelection(link);
			});
		});

		navigation.setAttribute("role", "tablist");

		const doctypeGroups = [
			[
				"الطلاب والقبول",
				[
					["طلبات القبول", "Dar Quraan Admission Application"],
					["الطلاب", "Dar Quraan Student"],
					["إسنادات الطلاب", "Dar Quraan Student Assignment"],
					["المواعيد الأسبوعية", "Dar Quraan Student Weekly Slot"],
				],
			],
			[
				"التعليم اليومي",
				[
					["الجلسات", "Dar Quraan Session"],
					["الحضور", "Dar Quraan Attendance"],
					["تقدم الطالب", "Dar Quraan Student Progress"],
					["حالة القرآن", "Dar Quraan Student Quran State"],
					["التكليف التالي", "Dar Quraan Next Assignment"],
					["تقدم المتون", "Dar Quraan Text Progress"],
				],
			],
			[
				"الجودة والرعاية",
				[
					["الاستثناءات", "Dar Quraan Exception"],
					["متابعة المعلم", "Dar Quraan Teacher Follow Up"],
					["زيارات الإشراف", "Dar Quraan Supervision Visit"],
					["الحوادث الانضباطية", "Dar Quraan Discipline Incident"],
				],
			],
			[
				"الاختبارات والشهادات",
				[
					["التقييمات", "Dar Quraan Evaluation"],
					["الاختبارات الرسمية", "Dar Quraan Exam"],
					["الإجازات", "Dar Quraan Ijazah"],
				],
			],
			[
				"التنظيم والإعداد",
				[
					["الفروع", "Dar Quraan Branch"],
					["مواقع التدريس", "Dar Quraan Teaching Location"],
					["المعلمون", "Dar Quraan Teacher"],
					["الحلقات", "Dar Quraan Halaqa"],
					["البرامج", "Dar Quraan Program"],
					["الإعدادات", "Dar Quraan Settings"],
				],
			],
		];

		const routeFor = (doctype) => `/app/${doctype.toLowerCase().replace(/ /g, "-")}`;
		const sidebar = document.createElement("aside");
		sidebar.className = "dq-guide-sidebar";
		sidebar.innerHTML = `<div class="dq-sidebar-heading"><strong>دليل سجلات النظام</strong><span>وصول مباشر إلى السجلات والقوائم</span></div><label class="dq-guide-search"><span>بحث</span><input type="search" placeholder="ابحث في سجلات النظام…" aria-label="البحث في سجلات نظام دار القرآن"></label><div class="dq-doctype-nav"></div>`;
		const doctypeNavigation = sidebar.querySelector(".dq-doctype-nav");

		doctypeGroups.forEach(([groupLabel, items]) => {
			const group = document.createElement("section");
			group.className = "dq-doctype-group";
			group.innerHTML = `<h3>${groupLabel}</h3>`;
			items.forEach(([label, doctype]) => {
				const link = document.createElement("a");
				link.href = routeFor(doctype);
				link.dataset.search = `${label} ${doctype}`.toLowerCase();
				link.innerHTML = `<span>${label}</span><small>عرض السجلات</small>`;
				group.appendChild(link);
			});
			doctypeNavigation.appendChild(group);
		});

		sidebar.querySelector("input").addEventListener("input", (event) => {
			const query = event.target.value.trim().toLowerCase();
			sidebar.querySelectorAll(".dq-doctype-group").forEach((group) => {
				let visible = 0;
				group.querySelectorAll("a").forEach((link) => {
					const matches = !query || link.dataset.search.includes(query);
					link.hidden = !matches;
					visible += Number(matches);
				});
				group.hidden = visible === 0;
			});
		});

		const layout = document.createElement("div");
		const main = document.createElement("div");
		layout.className = "dq-guide-layout";
		main.className = "dq-guide-main";
		Array.from(root.children).forEach((child) => main.appendChild(child));
		layout.append(sidebar, main);
		root.appendChild(layout);

		const hash = window.location.hash.slice(1);
		const initialLink = links.find((link) =>
			(link.dataset.sections || "").split(",").includes(hash)
		);

		if (initialLink) {
			showSelection(initialLink, false);
		}
	};

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", initialiseGuide);
	} else {
		initialiseGuide();
	}
})();
