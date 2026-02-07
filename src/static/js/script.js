// Main JavaScript file for additional functionality

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('GradAnalytics platform loaded');

    // ---------- AOS (Animate on Scroll) ----------
    AOS.init({
        duration: 800,
        easing: 'ease-out-cubic',
        once: true,
        offset: 80,
    });

    // ---------- Sticky header enhancement ----------
    const header = document.querySelector('header');

    window.addEventListener('scroll', function() {
        let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > 100) {
            header.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        } else {
            header.style.boxShadow = 'none';
        }
    });

    // ---------- Animated counter (hero stats) ----------
    function animateCounters() {
        document.querySelectorAll('.stat-number').forEach(counter => {
            const target = +counter.getAttribute('data-target');
            const duration = 2000; // ms
            const startTime = performance.now();

            function update(now) {
                const elapsed = now - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease-out quad
                const ease = 1 - (1 - progress) * (1 - progress);
                counter.textContent = Math.floor(ease * target);
                if (progress < 1) requestAnimationFrame(update);
                else counter.textContent = target;
            }

            requestAnimationFrame(update);
        });
    }

    // Trigger counters when hero section is visible
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        animateCounters();
                        observer.disconnect();
                    }
                });
            },
            { threshold: 0.3 }
        );
        observer.observe(heroSection);
    }

    // ---------- GSAP scroll-triggered section animations ----------
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
        gsap.registerPlugin(ScrollTrigger);

        // Parallax drift on hero background
        gsap.to('.hero', {
            backgroundPositionY: '30%',
            ease: 'none',
            scrollTrigger: {
                trigger: '.hero',
                start: 'top top',
                end: 'bottom top',
                scrub: true,
            },
        });

        // Dashboard sections fade-up (these don't have AOS attributes so no conflict)
        gsap.utils.toArray('.salary-trends-section, .university-comparison-section, .employment-trends-section').forEach(section => {
            const content = section.querySelector('.content');
            if (content) {
                gsap.from(content, {
                    scrollTrigger: {
                        trigger: section,
                        start: 'top 80%',
                    },
                    y: 40,
                    opacity: 0,
                    duration: 0.9,
                    ease: 'power2.out',
                });
            }
        });
    }

    // ---------- Magnetic hover effect on buttons ----------
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            btn.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = '';
        });
    });

    // ---------- Tilt effect on feature cards ----------
    document.querySelectorAll('.feature-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            card.style.transform = `perspective(800px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) translateY(-5px)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });
});