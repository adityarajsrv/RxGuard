import Header from "@/components/Header";
import Hero from "@/components/Hero";
import Method from "@/components/Method";
import CtaFooter from "@/components/CTAFooter";

export default function Home() {
  return (
    <>
      <div className="relative">
        <div
          className="absolute inset-x-0 top-0 -z-20 h-181.25 bg-cover bg-center opacity-60"
          style={{
            backgroundImage:
              "url('/pharmacy-shelf.jpg')",
          }}
        />
        <div className="absolute inset-x-0 top-0 -z-10 h-181.25 bg-linear-to-b from-black/50 via-black/80 to-black" />
        <Header />
        <Hero />
      </div>
      <main className="flex-1">
        <Method />
        <CtaFooter />
      </main>
    </>
  );
}