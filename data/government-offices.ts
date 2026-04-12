export interface GovernmentOffice {
  id: string
  names: Record<string, string> // keyed by ISO lang code: 'ms', 'en', 'id', etc.
  department_codes: string[] // codes the entity detector will match against
  address: string
  coordinates: { lat: number; lng: number }
  phone?: string // only include if verifiably correct
  operating_hours: {
    timezone: 'Asia/Kuala_Lumpur'
    schedule: {
      days: ('MON' | 'TUE' | 'WED' | 'THU' | 'FRI' | 'SAT' | 'SUN')[]
      open: string // 'HH:MM' 24h format
      close: string // 'HH:MM' 24h format
    }[]
    lunch_break?: { start: string; end: string; days: string[] }
    notes?: string
  }
  maps_place_id?: string // Google Maps Place ID if known
  official_url?: string
}

// Standard federal government schedule (Mon–Thu 08:00–17:00, Fri 08:00–16:45)
// with Mon–Thu lunch break 13:00–14:00 and Friday prayer break noted in notes.
const STANDARD_SCHEDULE: GovernmentOffice['operating_hours'] = {
  timezone: 'Asia/Kuala_Lumpur',
  schedule: [
    {
      days: ['MON', 'TUE', 'WED', 'THU'],
      open: '08:00',
      close: '17:00',
    },
    {
      days: ['FRI'],
      open: '08:00',
      close: '16:45',
    },
  ],
  lunch_break: {
    start: '13:00',
    end: '14:00',
    days: ['MON', 'TUE', 'WED', 'THU'],
  },
  notes: 'Friday prayer break approximately 12:15–14:45; counter services resume after break.',
}

export const GOVERNMENT_OFFICES: GovernmentOffice[] = [
  {
    id: 'jkm',
    names: {
      ms: 'Jabatan Kebajikan Masyarakat',
      en: 'Department of Social Welfare',
      id: 'Departemen Kesejahteraan Sosial',
    },
    department_codes: [
      'JKM',
      'Jabatan Kebajikan Masyarakat',
      'jabatan kebajikan',
      'jabatan kebajikan masyarakat',
      'Social Welfare Department',
      'Department of Social Welfare',
      'welfare department',
      'kebajikan masyarakat',
      'social welfare',
    ],
    address:
      'Aras 7, Blok E, Parcel E, Pusat Pentadbiran Kerajaan Persekutuan, 62520 Putrajaya',
    coordinates: { lat: 2.9247, lng: 101.6883 },
    operating_hours: STANDARD_SCHEDULE,
    official_url: 'https://www.jkm.gov.my',
  },

  {
    id: 'kwsp',
    names: {
      ms: 'Kumpulan Wang Simpanan Pekerja',
      en: 'Employees Provident Fund',
      id: 'Dana Provident Karyawan',
    },
    department_codes: [
      'KWSP',
      'EPF',
      'Kumpulan Wang Simpanan Pekerja',
      'Employees Provident Fund',
      'kumpulan wang simpanan',
      'dana simpanan pekerja',
      'employees provident',
      'provident fund',
    ],
    address: 'Bangunan KWSP, Jalan Raja Laut, 50350 Kuala Lumpur',
    coordinates: { lat: 3.154, lng: 101.6982 },
    operating_hours: {
      timezone: 'Asia/Kuala_Lumpur',
      schedule: [
        {
          days: ['MON', 'TUE', 'WED', 'THU', 'FRI'],
          open: '08:30',
          close: '17:30',
        },
      ],
      notes:
        'No formal lunch closure; however, service counters may have limited availability during lunch hours. Friday prayer break approximately 12:15–14:45.',
    },
    official_url: 'https://www.kwsp.gov.my',
  },

  {
    id: 'jtk',
    names: {
      ms: 'Jabatan Tenaga Kerja',
      en: 'Department of Labour',
      id: 'Departemen Tenaga Kerja',
    },
    department_codes: [
      'JTK',
      'JTKSM',
      'Jabatan Tenaga Kerja',
      'jabatan tenaga kerja',
      'Department of Labour',
      'Department of Labor',
      'labour department',
      'labor department',
      'tenaga kerja',
    ],
    address:
      'Blok D3, Parcel D, Pusat Pentadbiran Kerajaan Persekutuan, 62502 Putrajaya',
    coordinates: { lat: 2.9232, lng: 101.6857 },
    operating_hours: STANDARD_SCHEDULE,
    official_url: 'https://jtksm.mohr.gov.my',
  },

  {
    id: 'jpn',
    names: {
      ms: 'Jabatan Pendaftaran Negara',
      en: 'National Registration Department',
      id: 'Departemen Pendaftaran Nasional',
    },
    department_codes: [
      'JPN',
      'NRD',
      'Jabatan Pendaftaran Negara',
      'jabatan pendaftaran negara',
      'jabatan pendaftaran',
      'National Registration Department',
      'pendaftaran negara',
      'national registration',
    ],
    address:
      'Aras 1–7, Blok 2, Podium Presint 7, 62520 Putrajaya',
    coordinates: { lat: 2.9241, lng: 101.6877 },
    operating_hours: STANDARD_SCHEDULE,
    official_url: 'https://www.jpn.gov.my',
  },

  {
    id: 'kkm',
    names: {
      ms: 'Kementerian Kesihatan Malaysia',
      en: 'Ministry of Health Malaysia',
      id: 'Kementerian Kesehatan Malaysia',
    },
    department_codes: [
      'KKM',
      'MOH',
      'MySejahtera',
      'my sejahtera',
      'Kementerian Kesihatan Malaysia',
      'kementerian kesihatan',
      'Ministry of Health',
      'Ministry of Health Malaysia',
      'kesihatan malaysia',
      'mysejahtera',
    ],
    address:
      'Blok E7, Parcel E, Pusat Pentadbiran Kerajaan Persekutuan, Presint 1, 62590 Putrajaya',
    coordinates: { lat: 2.9356, lng: 101.6755 },
    operating_hours: STANDARD_SCHEDULE,
    official_url: 'https://www.moh.gov.my',
  },

  {
    id: 'nadma',
    names: {
      ms: 'Agensi Pengurusan Bencana Negara',
      en: 'National Disaster Management Agency',
      id: 'Badan Nasional Penanggulangan Bencana',
    },
    department_codes: [
      'NADMA',
      'Agensi Pengurusan Bencana Negara',
      'agensi pengurusan bencana',
      'National Disaster Management Agency',
      'disaster management',
      'agensi bencana',
      'national disaster',
    ],
    address:
      'Aras 5, Blok D5, Parcel D, Pusat Pentadbiran Kerajaan Persekutuan, 62502 Putrajaya',
    coordinates: { lat: 2.924, lng: 101.6852 },
    operating_hours: {
      ...STANDARD_SCHEDULE,
      notes:
        'Emergency operations centre staffed 24/7. Office hours listed are for administrative and general enquiries only. For disaster emergencies call 999.',
    },
    official_url: 'https://www.nadma.gov.my',
  },

  {
    id: 'lhdn',
    names: {
      ms: 'Lembaga Hasil Dalam Negeri Malaysia',
      en: 'Inland Revenue Board of Malaysia',
      id: 'Lembaga Pajak Dalam Negeri Malaysia',
    },
    department_codes: [
      'LHDN',
      'IRB',
      'IRBM',
      'Lembaga Hasil Dalam Negeri',
      'Lembaga Hasil Dalam Negeri Malaysia',
      'lembaga hasil',
      'hasil dalam negeri',
      'Inland Revenue Board',
      'Inland Revenue Board of Malaysia',
      'income tax',
      'cukai pendapatan',
    ],
    address:
      'Menara Hasil, Persiaran Rimba Permai, Cyber 8, 63000 Cyberjaya, Selangor',
    coordinates: { lat: 2.9262, lng: 101.6512 },
    operating_hours: STANDARD_SCHEDULE,
    official_url: 'https://www.hasil.gov.my',
  },

  {
    id: 'perkeso',
    names: {
      ms: 'Pertubuhan Keselamatan Sosial',
      en: 'Social Security Organisation',
      id: 'Organisasi Keamanan Sosial',
    },
    department_codes: [
      'SOCSO',
      'PERKESO',
      'Pertubuhan Keselamatan Sosial',
      'pertubuhan keselamatan sosial',
      'pertubuhan keselamatan',
      'keselamatan sosial',
      'Social Security Organisation',
      'Social Security Organization',
      'social security',
    ],
    address: 'Menara PERKESO, 281 Jalan Ampang, 50538 Kuala Lumpur',
    coordinates: { lat: 3.1607, lng: 101.7186 },
    operating_hours: STANDARD_SCHEDULE,
    official_url: 'https://www.perkeso.gov.my',
  },

  {
    id: 'imigresen',
    names: {
      ms: 'Jabatan Imigresen Malaysia',
      en: 'Immigration Department of Malaysia',
      id: 'Departemen Imigrasi Malaysia',
    },
    department_codes: [
      'JIM',
      'Imigresen',
      'imigresen',
      'Jabatan Imigresen',
      'Jabatan Imigresen Malaysia',
      'jabatan imigresen',
      'Immigration Department',
      'immigration department',
      'immigration',
      'imigrasi',
    ],
    address:
      'Blok 2G4, Presint 2, Pusat Pentadbiran Kerajaan Persekutuan, 62550 Putrajaya',
    coordinates: { lat: 2.9249, lng: 101.6739 },
    operating_hours: STANDARD_SCHEDULE,
    official_url: 'https://www.imi.gov.my',
  },

  {
    id: 'bomba',
    names: {
      ms: 'Jabatan Bomba dan Penyelamat Malaysia',
      en: 'Fire and Rescue Department of Malaysia',
      id: 'Departemen Pemadam Kebakaran Malaysia',
    },
    department_codes: [
      'BOMBA',
      'JBPM',
      'Jabatan Bomba',
      'Jabatan Bomba dan Penyelamat',
      'Jabatan Bomba dan Penyelamat Malaysia',
      'jabatan bomba',
      'bomba dan penyelamat',
      'Fire and Rescue Department',
      'fire and rescue',
      'fire department',
    ],
    address:
      'Ibu Pejabat JBPM, Jalan Diplomatik 3/1, Presint 15, 62050 Putrajaya',
    coordinates: { lat: 2.9133, lng: 101.6823 },
    operating_hours: {
      ...STANDARD_SCHEDULE,
      notes:
        'Emergency operations staffed 24/7. Office hours listed are for administrative enquiries only. For fire or rescue emergencies call 994.',
    },
    official_url: 'https://www.bomba.gov.my',
  },
]
