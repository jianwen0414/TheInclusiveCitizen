"use client"

import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"

const BAR_COUNT = 20
const MIN_HEIGHT = 6
const MAX_HEIGHT = 28
const SMOOTHING = 0.25

interface WaveformVisualizerProps {
  isRecording: boolean
  mediaStream?: MediaStream | null
}

export function WaveformVisualizer({ isRecording, mediaStream }: WaveformVisualizerProps) {
  const barRefs = useRef<(HTMLDivElement | null)[]>([])
  const rafId = useRef<number>(0)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const smoothedRef = useRef<number[]>(Array(BAR_COUNT).fill(MIN_HEIGHT))

  useEffect(() => {
    if (!isRecording || !mediaStream) return

    const audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
    const source = audioContext.createMediaStreamSource(mediaStream)
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    analyser.smoothingTimeConstant = 0.6
    analyser.minDecibels = -60
    analyser.maxDecibels = -10
    source.connect(analyser)

    audioContextRef.current = audioContext
    analyserRef.current = analyser
    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const update = () => {
      const analyserNode = analyserRef.current
      const bars = barRefs.current
      if (!analyserNode || !bars.length) return

      analyserNode.getByteFrequencyData(dataArray)
      const step = Math.floor(dataArray.length / BAR_COUNT)

      for (let i = 0; i < BAR_COUNT; i++) {
        const start = i * step
        let sum = 0
        for (let j = 0; j < step; j++) sum += dataArray[start + j] ?? 0
        const raw = step > 0 ? sum / step : 0
        const target = MIN_HEIGHT + (raw / 255) * (MAX_HEIGHT - MIN_HEIGHT)
        const prev = smoothedRef.current[i] ?? MIN_HEIGHT
        smoothedRef.current[i] = prev + (target - prev) * SMOOTHING
        const el = bars[i]
        if (el) el.style.height = `${Math.round(smoothedRef.current[i])}px`
      }

      rafId.current = requestAnimationFrame(update)
    }

    rafId.current = requestAnimationFrame(update)

    return () => {
      cancelAnimationFrame(rafId.current)
      try {
        audioContext.close()
      } catch (_) {}
      audioContextRef.current = null
      analyserRef.current = null
    }
  }, [isRecording, mediaStream])

  if (!isRecording) return null

  return (
    <div
      data-testid="voice-waveform"
      className="flex items-center justify-center gap-1 h-8 px-4"
      aria-hidden
    >
      {Array.from({ length: BAR_COUNT }).map((_, i) => (
        <div
          key={i}
          ref={(el) => {
            barRefs.current[i] = el
          }}
          className={cn(
            "w-1 bg-teal rounded-full transition-[height] duration-75 ease-out min-h-[6px]"
          )}
          style={{ height: `${MIN_HEIGHT}px` }}
        />
      ))}
    </div>
  )
}
