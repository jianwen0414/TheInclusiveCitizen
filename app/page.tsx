"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { PixelTrail } from "@/components/ui/pixel-trail"
import { BorderBeam } from "@/components/ui/border-beam"
import { useScreenSize } from "@/components/hooks/use-screen-size"

export default function LandingPage() {
  const screenSize = useScreenSize()

  return (
    <main className="relative w-full h-screen overflow-hidden bg-white">
      {/* PixelTrail Background – covers entire viewport, z-0 */}
      <div className="absolute inset-0 z-0">
        <PixelTrail
          pixelSize={screenSize.lessThan("md") ? 64 : 96}
          fadeDuration={0}
          delay={1200}
          pixelClassName="rounded-full bg-[#1A73E8]"
        />
      </div>

      {/* Centered content – z-10, always above pixels */}
      <div className="relative z-10 flex flex-col items-center justify-center w-full h-full pointer-events-none px-6">
        {/* BorderBeam card */}
        <div className="relative flex flex-col items-center justify-center rounded-2xl bg-white px-10 py-14 md:px-20 md:py-20 overflow-hidden shadow-xl">
          {/* Title */}
          <h1
            className="text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-semibold tracking-tight bg-gradient-to-b from-black to-gray-400/80 bg-clip-text text-transparent"
            style={{ letterSpacing: "-0.04em" }}
          >
            The Inclusive Citizen
          </h1>

          {/* Subtitle */}
          <p className="mt-4 md:mt-6 text-sm sm:text-base md:text-xl text-zinc-500 max-w-xl text-center">
            Government services made accessible for everyone, in every language.
          </p>

          {/* CTA button */}
          <div className="pointer-events-auto mt-8 md:mt-10">
            <Link href="/chat">
              <Button
                size="lg"
                className="rounded-full px-8 py-6 text-base font-medium transition-all shadow-md hover:shadow-lg bg-zinc-900 text-white hover:bg-zinc-800"
              >
                Get Started
              </Button>
            </Link>
          </div>

          {/* Border beam effect */}
          <BorderBeam size={250} duration={12} delay={9} />
        </div>

        {/* Footer attribution */}
        <p className="absolute text-xs md:text-base bottom-4 right-4 text-zinc-400 pointer-events-none">
          V Hack 2026 — USM
        </p>
      </div>
    </main>
  )
}
