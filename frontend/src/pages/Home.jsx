import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import About from '../components/About';
import Features from '../components/Features';
import Pricing from '../components/Pricing';
import Location from '../components/Location';
import Contact from '../components/Contact';
import Footer from '../components/Footer';
import BookingModal from '../components/BookingModal';

export default function Home() {
  const [bookingOpen, setBookingOpen] = useState(false);
  const openBooking = () => setBookingOpen(true);
  return (
    <div className="bg-[#EFE9DE]">
      <Navbar onBook={openBooking} />
      <Hero onBook={openBooking} />
      <About />
      <Features />
      <Pricing onBook={openBooking} />
      <Location />
      <Contact />
      <Footer />
      <BookingModal open={bookingOpen} onClose={() => setBookingOpen(false)} />
    </div>
  );
}
