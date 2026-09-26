import CtaFooter from "@/components/CTAFooter";
import Header from "@/components/Header";
import VerificationBench from "@/components/VerificationBench";

export default function VerifyPage() {
  return (
    <>
      <Header />
      <main className="flex-1">
        <VerificationBench />
        <CtaFooter />
      </main>
    </>
  );
}