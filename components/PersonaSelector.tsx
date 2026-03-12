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
    bgColor: "bg-blue-tint",
  },
  {
    id: "migrant" as Persona,
    icon: HardHat,
    title: "Migrant Worker",
    bgColor: "bg-red-tint",
  },
  {
    id: "rural" as Persona,
    icon: TreePine,
    title: "Rural Community",
    bgColor: "bg-green-tint",
  }
]

export function PersonaSelector({ selectedPersona, onSelectPersona }: PersonaSelectorProps) {
  return (
    <div className="flex flex-col">
      {personas.map((persona) => {
        const Icon = persona.icon
        const isSelected = selectedPersona === persona.id
        return (
          <button
            key={persona.id}
            onClick={() => onSelectPersona(persona.id)}
            className={cn(
              "flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-150 text-left",
              isSelected
                ? "bg-blue-tint text-primary"
                : "hover:bg-border-subtle text-text-primary"
            )}
          >
            <div
              className={cn(
                "flex items-center justify-center w-4 h-4 rounded shrink-0",
                persona.bgColor
              )}
            >
              <Icon className="w-2.5 h-2.5 text-text-primary" />
            </div>
            <span className={cn(
              "text-sm font-medium",
              isSelected && "text-primary"
            )}>
              {persona.title}
            </span>
          </button>
        )
      })}
    </div>
  )
}
