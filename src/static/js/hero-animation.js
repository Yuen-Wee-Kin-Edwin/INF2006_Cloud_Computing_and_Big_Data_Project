// Three.js Interactive Particle Network Background
(function () {
    const canvas = document.getElementById('heroCanvas');
    if (!canvas) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });

    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // --- Particles ---
    const PARTICLE_COUNT = 120;
    const SPREAD = 30;
    const positions = new Float32Array(PARTICLE_COUNT * 3);
    const velocities = [];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        positions[i * 3]     = (Math.random() - 0.5) * SPREAD;
        positions[i * 3 + 1] = (Math.random() - 0.5) * SPREAD;
        positions[i * 3 + 2] = (Math.random() - 0.5) * SPREAD * 0.5;
        velocities.push({
            x: (Math.random() - 0.5) * 0.015,
            y: (Math.random() - 0.5) * 0.015,
            z: (Math.random() - 0.5) * 0.008,
        });
    }

    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const particleMaterial = new THREE.PointsMaterial({
        color: 0x3b82f6,
        size: 0.12,
        transparent: true,
        opacity: 0.8,
        sizeAttenuation: true,
    });

    const particlesMesh = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particlesMesh);

    // --- Connection lines ---
    const LINE_DISTANCE = 4.5;
    const lineGeometry = new THREE.BufferGeometry();
    const maxLines = PARTICLE_COUNT * PARTICLE_COUNT;
    const linePositions = new Float32Array(maxLines * 6);
    const lineColors = new Float32Array(maxLines * 6);
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    lineGeometry.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));

    const lineMaterial = new THREE.LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.4,
        blending: THREE.AdditiveBlending,
    });

    const linesMesh = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(linesMesh);

    camera.position.z = 15;

    // --- Mouse interaction ---
    const mouse = { x: 0, y: 0 };

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    });

    // --- Animate ---
    function animate() {
        requestAnimationFrame(animate);

        const pos = particleGeometry.attributes.position.array;

        // Move particles
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            pos[i * 3]     += velocities[i].x;
            pos[i * 3 + 1] += velocities[i].y;
            pos[i * 3 + 2] += velocities[i].z;

            // Bounce at boundaries
            if (Math.abs(pos[i * 3])     > SPREAD / 2) velocities[i].x *= -1;
            if (Math.abs(pos[i * 3 + 1]) > SPREAD / 2) velocities[i].y *= -1;
            if (Math.abs(pos[i * 3 + 2]) > SPREAD / 4) velocities[i].z *= -1;
        }

        particleGeometry.attributes.position.needsUpdate = true;

        // Draw connection lines between nearby particles
        let lineIndex = 0;
        const lp = lineGeometry.attributes.position.array;
        const lc = lineGeometry.attributes.color.array;

        for (let i = 0; i < PARTICLE_COUNT; i++) {
            for (let j = i + 1; j < PARTICLE_COUNT; j++) {
                const dx = pos[i * 3]     - pos[j * 3];
                const dy = pos[i * 3 + 1] - pos[j * 3 + 1];
                const dz = pos[i * 3 + 2] - pos[j * 3 + 2];
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

                if (dist < LINE_DISTANCE) {
                    const alpha = 1 - dist / LINE_DISTANCE;

                    lp[lineIndex * 6]     = pos[i * 3];
                    lp[lineIndex * 6 + 1] = pos[i * 3 + 1];
                    lp[lineIndex * 6 + 2] = pos[i * 3 + 2];
                    lp[lineIndex * 6 + 3] = pos[j * 3];
                    lp[lineIndex * 6 + 4] = pos[j * 3 + 1];
                    lp[lineIndex * 6 + 5] = pos[j * 3 + 2];

                    // Gradient blue color
                    lc[lineIndex * 6]     = 0.23 * alpha;
                    lc[lineIndex * 6 + 1] = 0.51 * alpha;
                    lc[lineIndex * 6 + 2] = 0.96 * alpha;
                    lc[lineIndex * 6 + 3] = 0.23 * alpha;
                    lc[lineIndex * 6 + 4] = 0.51 * alpha;
                    lc[lineIndex * 6 + 5] = 0.96 * alpha;

                    lineIndex++;
                }
            }
        }

        lineGeometry.setDrawRange(0, lineIndex * 2);
        lineGeometry.attributes.position.needsUpdate = true;
        lineGeometry.attributes.color.needsUpdate = true;

        // Mouse parallax effect
        particlesMesh.rotation.y += (mouse.x * 0.3 - particlesMesh.rotation.y) * 0.02;
        particlesMesh.rotation.x += (mouse.y * 0.3 - particlesMesh.rotation.x) * 0.02;
        linesMesh.rotation.y = particlesMesh.rotation.y;
        linesMesh.rotation.x = particlesMesh.rotation.x;

        // Slow auto-rotation
        particlesMesh.rotation.y += 0.001;
        linesMesh.rotation.y += 0.001;

        renderer.render(scene, camera);
    }

    animate();

    // --- Resize handler ---
    window.addEventListener('resize', () => {
        const hero = document.querySelector('.hero');
        if (!hero) return;
        const width = hero.clientWidth;
        const height = hero.clientHeight;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    });
})();
