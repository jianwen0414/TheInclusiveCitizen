"use client"

import { useEffect, useRef, useCallback } from "react"

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  color: string
  originalX: number
  originalY: number
  angle: number
  speed: number
}

const PARTICLE_COLORS = [
  "#4285F4", // Google Blue
  "#4285F4",
  "#4285F4",
  "#7B61FF", // Purple
  "#7B61FF",
  "#E8453C", // Coral
  "#F4B400", // Yellow (occasional)
]

export function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Particle[]>([])
  const mouseRef = useRef({ x: 0, y: 0 })
  const animationRef = useRef<number>()

  const createParticles = useCallback((width: number, height: number) => {
    const particles: Particle[] = []
    const numParticles = Math.floor((width * height) / 8000) // density based on screen size
    
    for (let i = 0; i < numParticles; i++) {
      const x = Math.random() * width
      const y = Math.random() * height
      particles.push({
        x,
        y,
        vx: 0,
        vy: 0,
        size: Math.random() * 3 + 1.5,
        color: PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)],
        originalX: x,
        originalY: y,
        angle: Math.random() * Math.PI * 2,
        speed: Math.random() * 0.3 + 0.1
      })
    }
    return particles
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const handleResize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      particlesRef.current = createParticles(canvas.width, canvas.height)
    }

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY }
    }

    handleResize()
    window.addEventListener("resize", handleResize)
    window.addEventListener("mousemove", handleMouseMove)

    const animate = () => {
      if (!ctx || !canvas) return

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const mouseX = mouseRef.current.x
      const mouseY = mouseRef.current.y
      const influenceRadius = 200

      particlesRef.current.forEach((particle) => {
        // Calculate distance from mouse
        const dx = mouseX - particle.x
        const dy = mouseY - particle.y
        const distance = Math.sqrt(dx * dx + dy * dy)

        // Mouse influence - particles flow away smoothly
        if (distance < influenceRadius && distance > 0) {
          const force = (influenceRadius - distance) / influenceRadius
          const angle = Math.atan2(dy, dx)
          // Push particles away from cursor
          particle.vx -= Math.cos(angle) * force * 2
          particle.vy -= Math.sin(angle) * force * 2
        }

        // Gentle drift animation
        particle.angle += 0.01
        const driftX = Math.cos(particle.angle) * particle.speed * 0.5
        const driftY = Math.sin(particle.angle) * particle.speed * 0.5

        // Return to original position with spring effect
        const returnForce = 0.02
        particle.vx += (particle.originalX - particle.x) * returnForce + driftX
        particle.vy += (particle.originalY - particle.y) * returnForce + driftY

        // Apply friction
        particle.vx *= 0.92
        particle.vy *= 0.92

        // Update position
        particle.x += particle.vx
        particle.y += particle.vy

        // Draw particle as a small dash/line (like in Antigravity)
        ctx.save()
        ctx.translate(particle.x, particle.y)
        
        // Rotate based on velocity or angle
        const rotation = Math.atan2(particle.vy, particle.vx) || particle.angle
        ctx.rotate(rotation)

        // Draw dash
        ctx.beginPath()
        ctx.moveTo(-particle.size * 1.5, 0)
        ctx.lineTo(particle.size * 1.5, 0)
        ctx.strokeStyle = particle.color
        ctx.lineWidth = particle.size * 0.6
        ctx.lineCap = "round"
        ctx.stroke()
        
        ctx.restore()
      })

      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener("resize", handleResize)
      window.removeEventListener("mousemove", handleMouseMove)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [createParticles])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      style={{ background: "transparent" }}
    />
  )
}
