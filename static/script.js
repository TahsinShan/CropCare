
  function toggleMenu() {
    const menu = document.getElementById("navbarMenu");
    menu.classList.toggle("active");
  }
  // Change navbar on scroll
  window.addEventListener('scroll', function () {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 10) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });
