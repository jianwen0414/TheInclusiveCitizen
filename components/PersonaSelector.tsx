"use client"

import { User, HardHat, TreePine } from "lucide-react"
import { cn } from "@/lib/utils"

export type Persona = "elderly" | "migrant" | "rural"

interface PersonaSelectorProps {
  selectedPersona: Persona
  onSelectPersona: (persona: Persona) => void
}

const personas = [
  {
    id: "elderly" as Persona,
    icon: User,
    title: "Elderly",
    subtitle: "Warga Emas",
    description: "Larger text, voice-first"
  },
  {
    id: "migrant" as Persona,
    icon: HardHat,
    title: "Migrant Worker",
    subtitle: "Pekerja Migran",
    description: "Multi-language support"
  },
  {
    id: "rural" as Persona,
    icon: TreePine,
    title: "Rural Community",
    subtitle: "Luar Bandar",
    description: "Voice & visual guides"
  }
]

export function PersonaSelector({ selectedPersona, onSelectPersona }: PersonaSelectorProps) {
  return (
    <div className="flex flex-col gap-3">
      <h3 className="font-heading text-sm font-semibold text-primary uppercase tracking-wide">
        Select Your Profile
      </h3>
      <div className="flex flex-col gap-2">
        {personas.map((persona) => {
          const Icon = persona.icon
          const isSelected = selectedPersona === persona.id
          return (
            <button
              key={persona.id}
              onClick={() => onSelectPersona(persona.id)}
              className={cn(
                "flex items-start gap-3 p-4 rounded-xl border-2 transition-all text-left",
                "hover:border-accent hover:bg-indigo/50",
                isSelected
                  ? "border-accent bg-indigo shadow-sm"
                  : "border-transparent bg-card"
              )}
            >
              <div
                className={cn(
                  "flex items-center justify-center w-10 h-10 rounded-lg shrink-0",
                  isSelected ? "bg-accent text-accent-foreground" : "bg-muted text-primary"
                )}
              >
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex flex-col gap-0.5">
                <span className={cn(
                  "font-heading font-bold",
                  isSelected ? "text-primary" : "text-primary/80"
                )}>
                  {persona.title}
                </span>
                <span className="text-sm text-muted-foreground">
                  {persona.subtitle}
                </span>
                <span className="text-xs text-muted-foreground mt-1">
                  {persona.description}
                </span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
