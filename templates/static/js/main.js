/* --------------------------------------------------------------------------
   AnyRent interactions — local-only demo behavior with accessible live status.
   -------------------------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  const searchForm = document.querySelector("#search");
  const searchStatus = document.querySelector("#search-status");
  const category = document.querySelector("#category");
  const locationInput = document.querySelector("#location");
  const startDate = document.querySelector("#start-date");
  const endDate = document.querySelector("#end-date");
  const newsletterForm = document.querySelector("#newsletter");
  const newsletterEmail = document.querySelector("#newsletter-email");
  const newsletterStatus = document.querySelector("#newsletter-status");
  const navLinks = [...document.querySelectorAll("#navLinks .nav-link")];
  const collapseElement = document.querySelector("#mainNav");
  // Set sensible date bounds so the demo form does not accept dates in the past.
  if (startDate && endDate) {
    const today = new Date();
    const todayString = today.toISOString().split("T")[0];
    startDate.min = todayString;
    endDate.min = todayString;

    startDate.addEventListener("change", () => {
      endDate.min = startDate.value || todayString;
      if (endDate.value && startDate.value && endDate.value < startDate.value) {
        endDate.value = startDate.value;
      }
    });
  }

  // Search feedback is intentionally local: it confirms a useful result without a backend.
  if (searchForm && searchStatus && endDate && startDate) {
    searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      searchStatus.classList.remove("error");

      if (!searchForm.checkValidity()) {
        searchStatus.textContent = "Choose a category, location, and rental dates to search.";
        searchStatus.classList.add("error");
        searchForm.reportValidity();
        return;
      }

      if (endDate.value < startDate.value) {
        searchStatus.textContent = "Your return date needs to be after your start date.";
        searchStatus.classList.add("error");
        endDate.focus();
        return;
      }

      const categoryName = category.options[category.selectedIndex].text;
      const place = locationInput.value.trim();
      searchStatus.textContent = `Searching ${categoryName.toLowerCase()} near ${place} for your selected dates…`;
    });
  }

  // Small email capture validation with feedback announced to screen readers.
  if (newsletterForm && newsletterEmail && newsletterStatus) {
    newsletterForm.addEventListener("submit", (event) => {
      event.preventDefault();
      newsletterStatus.classList.remove("error");

      if (!newsletterEmail.validity.valid) {
        newsletterStatus.textContent = "Enter a valid email address to join the list.";
        newsletterStatus.classList.add("error");
        newsletterEmail.focus();
        return;
      }

      newsletterStatus.textContent = "You’re in! Watch your inbox for your first AnyRent note.";
      newsletterForm.reset();
    });
  }

  // Fade sections into view as they enter the viewport.
  const revealElements = document.querySelectorAll(".reveal");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealElements.forEach((element) => element.classList.add("is-visible"));
  } else {
    const observer = new IntersectionObserver((entries, currentObserver) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          currentObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealElements.forEach((element) => observer.observe(element));
  }

  // Keep the navigation's visual active state aligned with the visible section.
  const navTargets = navLinks
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);
  if (navLinks.length && "IntersectionObserver" in window) {
    const navObserver = new IntersectionObserver((entries) => {
      const visibleEntry = entries.find((entry) => entry.isIntersecting);
      if (!visibleEntry) return;
      navLinks.forEach((link) => {
        const isCurrent = link.getAttribute("href") === `#${visibleEntry.target.id}`;
        link.classList.toggle("active", isCurrent);
        if (isCurrent) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
      });
    }, { rootMargin: "-20% 0px -65% 0px", threshold: 0 });
    navTargets.forEach((target) => navObserver.observe(target));
  }

  // Collapse the mobile menu after a destination is chosen.
  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      if (window.bootstrap && window.innerWidth < 992 && collapseElement.classList.contains("show")) {
        window.bootstrap.Collapse.getOrCreateInstance(collapseElement).hide();
      }
    });
  });

  document.querySelector("#current-year").textContent = String(new Date().getFullYear());
});
