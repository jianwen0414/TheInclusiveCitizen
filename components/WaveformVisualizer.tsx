"use client"

import { cn } from "@/lib/utils"

interface WaveformVisualizerProps {
  isRecording: boolean
}

export function WaveformVisualizer({ isRecording }: WaveformVisualizerProps) {
  if (!isRecording) return null

  return (
    <div className="flex items-center justify-center gap-1 h-8 px-4">
      {Array.from({ length: 20 }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "w-1 bg-teal rounded-full transition-all",
            "animate-[waveform_0.5s_ease-in-out_infinite]"
          )}
          style={{
            height: `${Math.random() * 24 + 8}px`,
            animationDelay: `${i * 0.05}s`
          }}
        />
      ))}
    </div>
  )
}
