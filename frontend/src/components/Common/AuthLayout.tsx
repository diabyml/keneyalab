import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import { Footer } from "./Footer"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh bg-background lg:grid-cols-[1.1fr_0.9fr]">
      <div className="relative hidden overflow-hidden bg-[#102A2E] text-white lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div
          aria-hidden="true"
          className="absolute inset-0 opacity-20 [background-image:linear-gradient(rgb(50_184_198_/_0.18)_1px,transparent_1px),linear-gradient(90deg,rgb(50_184_198_/_0.18)_1px,transparent_1px)] [background-size:40px_40px]"
        />
        <Logo variant="full" className="relative z-10 text-xl" asLink={false} />
        <div className="relative z-10 max-w-xl">
          <div className="mb-6 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.18em] text-[#8DE5E8]">
            <span className="h-px w-10 bg-[#32B8C6]" />
            Poste clinique sécurisé
          </div>
          <h2 className="font-heading text-4xl font-semibold leading-tight tracking-[-0.04em]">
            Chaque échantillon mérite une traçabilité sans faille.
          </h2>
          <p className="mt-5 max-w-lg text-sm leading-6 text-white/65">
            Pilotez les demandes, prélèvements, résultats et validations depuis
            un espace de travail conçu pour le rythme du laboratoire.
          </p>
          <div className="mt-10 grid max-w-lg grid-cols-3 gap-3">
            {["Traçabilité", "Validation", "Confidentialité"].map((label) => (
              <div
                key={label}
                className="border-l-2 border-[#32B8C6] bg-white/[0.045] px-3 py-2 text-xs font-medium text-white/80"
              >
                {label}
              </div>
            ))}
          </div>
        </div>
        <p className="relative z-10 text-xs text-white/40">
          KeneyaLab · Laboratoire connecté
        </p>
      </div>
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex justify-end">
          <Appearance />
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-sm rounded-2xl border border-border/80 bg-card p-6 shadow-[var(--shadow-card)] sm:p-8">
            <div className="mb-8 lg:hidden">
              <Logo variant="full" asLink={false} />
            </div>
            {children}
          </div>
        </div>
        <Footer />
      </div>
    </div>
  )
}
