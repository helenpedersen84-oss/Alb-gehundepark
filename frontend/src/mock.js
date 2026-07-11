// Mock data + helpers for Albøge Hundepark clone (frontend-only phase)

export const CONTENT = {
  brand: 'Albøge Hundepark',
  nav: [
    { label: 'Om os', href: '#om' },
    { label: 'Hvad vi tilbyder', href: '#faciliteter' },
    { label: 'Priser', href: '#priser' },
    { label: 'Kontakt', href: '#kontakt' },
  ],
  hero: {
    kicker: 'ALBØGE HUNDEPARK',
    title1: 'Frihed',
    title2: 'i det Fri',
    subtitle: 'Et naturskønt fristed hvor hunde løber frit — omgivet af åbne marker og frisk luft.',
    image: 'https://media.base44.com/images/public/6a2311b51edab6475c318617/7a6ec850b_generated_6aba4359.png',
  },
  about: {
    kicker: 'OM PARKEN',
    title1: 'Et sted skabt til',
    title2: 'naturlig glæde',
    p1: 'Albøge Hundepark er et indhegnet naturområde i det smukke østjyske landskab, hvor din hund kan løbe frit og udforske naturen i trygge omgivelser.',
    p2: 'Parken tilbyder åbne marker, naturlige stier og masser af plads til leg og motion — alt sammen omgivet af den smukke Djurslandske natur.',
    image: 'https://media.base44.com/images/public/6a2311b51edab6475c318617/dcaae070d_generated_a26e5ecd.png',
  },
  features: {
    kicker: 'HVAD VI TILBYDER',
    title1: 'Alt hvad din hund',
    title2: 'har brug for',
    items: [
      { icon: 'Home', title: 'Indhegnet areal', text: 'Fuldstændigt aflukket og sikkert areal, så din hund kan løbe frit uden snor.' },
      { icon: 'Leaf', title: 'Naturlige omgivelser', text: 'Grønt og naturligt miljø med plads til at snuse, grave og udforske.' },
      { icon: 'ToyBrick', title: 'Legeudstyr', text: 'Forhindringsbaner, bolde og legesager der stimulerer hunden mentalt og fysisk.' },
      { icon: 'Droplets', title: 'Frisk vand', text: 'Altid adgang til frisk drikkevand til din hund under opholdet.' },
      { icon: 'ParkingCircle', title: 'Nem parkering', text: 'Gratis parkering lige ved pladsen – nem adgang med bil.' },
      { icon: 'CalendarCheck', title: 'Fleksibel booking', text: 'Book din tid online – vælg det tidspunkt der passer dig og din hund bedst.' },
      { icon: 'Smartphone', title: 'Betaling via kort', text: 'Vi modtager betaling nemt og hurtigt med betalingskort.' },
    ],
  },
  pricing: {
    kicker: 'PRISER',
    title1: 'Enkle og ærlige',
    title2: 'priser',
    subtitle: 'Ingen skjulte gebyrer – betal for den tid I har brug for.',
    plans: [
      {
        name: 'Enkeltbesøg', price: '60 kr.', unit: 'pr. time / 1 hund', popular: false,
        desc: 'Perfekt til den spontane legetur. Ekstra hunde tilføjes for 30 kr. pr. styk.',
        features: ['1 hund inkluderet', 'Valgfri varighed', 'Ekstra hund: 30 kr.', 'Gratis parkering'],
        cta: 'Book nu',
      },
      {
        name: '10-turskort', price: '560 kr.', unit: 'spar ~7%', popular: true,
        desc: 'Få 10 besøg med rabat. Perfekt til den regelmæssige gæst.',
        features: ['10 besøg inkluderet', '56 kr. pr. besøg', 'Gyldigt i 6 måneder', 'Gratis parkering'],
        cta: 'Book nu',
      },
      {
        name: 'Heldagsleje', price: 'Kontakt os', unit: 'for pris og info', popular: false,
        desc: 'Parken kan lejes til træning, kurser og andre arrangementer hele dagen.',
        features: ['Eksklusiv adgang hele dagen', 'Egnet til træning og kurser', 'Fleksible muligheder', 'Kontakt for aftale'],
        cta: 'Kontakt os',
      },
    ],
  },
  location: {
    kicker: 'LOKATION',
    title1: 'Find vej til',
    title2: 'Albøge',
    image: 'https://media.base44.com/images/public/6a2311b51edab6475c318617/253c9ee6f_generated_1a1df63b.png',
    address: ['Askhøjvej 64', '8570 Trustrup', 'Djursland, Østjylland'],
    hours: ['Åben hele året', 'Solopgang til solnedgang'],
    parking: ['Gratis parkering', 'lige ved indgangen'],
    destination: 'Askhøjvej 64, 8570 Trustrup, Danmark',
    lat: 56.361263, lng: 10.703126,
  },
  contact: {
    kicker: 'KONTAKT',
    title1: 'Kom i kontakt',
    title2: 'med os',
    subtitle: 'Har du spørgsmål til booking, priser eller pladsen? Vi vender tilbage hurtigst muligt.',
    address: 'Albøge, 8500 Grenaa, Djursland',
    phone: '+45 93 84 18 68',
    email: 'hej@albogehundepark.dk',
  },
};

// Booking config
export const BOOKING = {
  openHour: 5,   // 05:00
  closeHour: 22, // last slot starts 21:00 -> ends 21:45 (before 22:00)
  sessionMinutes: 45,
  pricePerBooking: 60, // DKK
};

// Build slots for a day: 05:00, 06:00 ... 21:00. Each 45 min session.
export function buildSlots() {
  const slots = [];
  for (let h = BOOKING.openHour; h < BOOKING.closeHour; h++) {
    const start = `${String(h).padStart(2, '0')}:00`;
    const end = `${String(h).padStart(2, '0')}:45`;
    slots.push({ hour: h, start, end, label: `${start} – ${end}` });
  }
  return slots;
}

// Mock in-memory slot status for frontend-only phase
export function mockSlotStatuses() {
  return {}; // {'2025-07-12T10': 'booked' | 'locked'}
}
