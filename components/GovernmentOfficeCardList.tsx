"use client"

import type { GovernmentOffice } from '@/data/government-offices'
import { GovernmentOfficeCard } from './GovernmentOfficeCard'

const HEADING: Record<string, string> = {
  en: 'Relevant Government Offices',
  ms: 'Pejabat Kerajaan Berkaitan',
  id: 'Kantor Pemerintah Terkait',
}

export interface GovernmentOfficeCardListProps {
  offices: GovernmentOffice[]
  detectedLanguage: string
}

export function GovernmentOfficeCardList({
  offices,
  detectedLanguage,
}: GovernmentOfficeCardListProps) {
  if (offices.length === 0) return null

  const baseLang = detectedLanguage.split('-')[0]
  const heading = HEADING[baseLang] ?? HEADING['en']

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">
        {heading}
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {offices.map((office) => (
          <GovernmentOfficeCard
            key={office.id}
            office={office}
            detectedLanguage={detectedLanguage}
          />
        ))}
      </div>
    </div>
  )
}
