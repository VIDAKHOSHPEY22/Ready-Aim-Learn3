/**
 * Ready Aim Learn - Main JavaScript File
 * Contains all interactive functionality for the website
 */

document.addEventListener('DOMContentLoaded', function() {
    // ========== Mobile Navigation Toggle ==========
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const navLinks = document.querySelectorAll('.nav-links li a');
    const mobileNav = document.createElement('div');
    const overlay = document.createElement('div');
    
    // Create mobile nav elements
    function createMobileNav() {
        // Create overlay
        overlay.className = 'overlay';
        document.body.appendChild(overlay);
        
        // Create mobile nav
        mobileNav.className = 'mobile-nav';
        mobileNav.innerHTML = `
            <div class="mobile-nav-header">
                <img src="${document.querySelector('.logo').src}" alt="Ready Aim Learn Logo" class="mobile-logo">
                <button class="mobile-close"><i class="fas fa-times"></i></button>
            </div>
            <ul class="mobile-nav-links">
                ${Array.from(document.querySelectorAll('.nav-links li')).map(li => li.outerHTML).join('')}
            </ul>
        `;
        document.body.appendChild(mobileNav);
        
        // Close buttons
        const closeBtn = document.querySelector('.mobile-close');
        closeBtn.addEventListener('click', toggleMobileNav);
        overlay.addEventListener('click', toggleMobileNav);
    }
    
    // Toggle mobile nav function
    function toggleMobileNav() {
        mobileNav.classList.toggle('active');
        overlay.classList.toggle('active');
        document.body.classList.toggle('no-scroll');
        menuToggle.classList.toggle('active');
    }
    
    // Initialize mobile nav
    createMobileNav();
    menuToggle.addEventListener('click', toggleMobileNav);
    
    // Close mobile nav when clicking on links
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (mobileNav.classList.contains('active')) {
                toggleMobileNav();
            }
        });
    });
    
    // ========== Sticky Header ==========
    const header = document.querySelector('.site-header');
    const headerHeight = header.offsetHeight;
    
    function handleScroll() {
        if (window.scrollY > headerHeight) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }
    
    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Run once on load
    
    // ========== Smooth Scrolling ==========
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - headerHeight,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // ========== Testimonial Slider ==========
    const testimonialSlider = () => {
        const testimonialCards = document.querySelectorAll('.testimonial-card');
        if (testimonialCards.length < 2) return;
        
        let currentIndex = 0;
        const totalTestimonials = testimonialCards.length;
        
        function showTestimonial(index) {
            testimonialCards.forEach((card, i) => {
                card.style.opacity = i === index ? '1' : '0';
                card.style.pointerEvents = i === index ? 'all' : 'none';
                card.style.transform = i === index ? 'translateY(0)' : 'translateY(20px)';
                card.style.position = i === index ? 'relative' : 'absolute';
            });
        }
        
        function nextTestimonial() {
            currentIndex = (currentIndex + 1) % totalTestimonials;
            showTestimonial(currentIndex);
        }
        
        // Auto-rotate testimonials every 5 seconds
        let sliderInterval = setInterval(nextTestimonial, 5000);
        
        // Pause on hover
        const testimonialSection = document.querySelector('.testimonials-section');
        testimonialSection.addEventListener('mouseenter', () => {
            clearInterval(sliderInterval);
        });
        
        testimonialSection.addEventListener('mouseleave', () => {
            sliderInterval = setInterval(nextTestimonial, 5000);
        });
        
        // Initial display
        showTestimonial(currentIndex);
    };
    
    testimonialSlider();
    
    // ========== Gallery Hover Effect ==========
    const galleryItems = document.querySelectorAll('.gallery-item');
    galleryItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            if (window.innerWidth > 768) { // Only on desktop
                item.querySelector('img').style.transform = 'scale(1.1)';
                item.querySelector('.gallery-overlay').style.transform = 'translateY(0)';
            }
        });
        
        item.addEventListener('mouseleave', () => {
            if (window.innerWidth > 768) {
                item.querySelector('img').style.transform = 'scale(1)';
                item.querySelector('.gallery-overlay').style.transform = 'translateY(100%)';
            }
        });
    });
    
    // ========== Service Card Animation ==========
    const serviceCards = document.querySelectorAll('.service-card');
    serviceCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.querySelector('.service-icon').style.transform = 'scale(1.1) rotate(10deg)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.querySelector('.service-icon').style.transform = 'scale(1) rotate(0)';
        });
    });
    
    // ========== Scroll Reveal Animation ==========
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.service-card, .gallery-item, .testimonial-card, .section-title');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1
        });
        
        elements.forEach(element => {
            observer.observe(element);
        });
    };
    
    animateOnScroll();
    
    // ========== Dynamic Year for Footer ==========
    document.querySelector('.copyright').innerHTML = `&copy; ${new Date().getFullYear()} Ready Aim Learn. All rights reserved. | <a href="{% url 'legal' %}">Terms & Waiver</a> | <a href="{% url 'privacy' %}">Privacy Policy</a>`;
    
    // ========== Phone Number Formatting ==========
    const phoneLinks = document.querySelectorAll('a[href^="tel:"]');
    phoneLinks.forEach(link => {
        const phoneNumber = link.getAttribute('href').replace('tel:', '');
        const formattedNumber = formatPhoneNumber(phoneNumber);
        link.textContent = link.textContent.replace(phoneNumber, formattedNumber);
    });
    
    function formatPhoneNumber(phoneNumber) {
        // Simple formatting for US numbers
        const cleaned = ('' + phoneNumber).replace(/\D/g, '');
        const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
        if (match) {
            return `(${match[1]}) ${match[2]}-${match[3]}`;
        }
        return phoneNumber;
    }
});

// ========== Preloader ==========
window.addEventListener('load', function() {
    const preloader = document.querySelector('.preloader');
    if (preloader) {
        preloader.style.transition = 'opacity 0.5s ease';
        preloader.style.opacity = '0';
        setTimeout(() => {
            preloader.style.display = 'none';
        }, 500);
    }
});