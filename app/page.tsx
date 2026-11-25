import Image from "next/image";
import { ArrowDown, Search } from "lucide-react";
import { Catalog } from "@/components/catalog";
import { ThemeToggle } from "@/components/theme-toggle";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto min-h-screen max-w-6xl px-5 sm:px-8">
        <header className="sticky top-0 z-20 -mx-5 flex h-14 items-center justify-between border-b border-border bg-background px-5 sm:-mx-8 sm:px-8">
          <div className="flex items-center gap-3">
            <Image
              alt=""
              aria-hidden="true"
              className="h-7 w-7 object-contain"
              height={28}
              src="/branding/logo-biblioteca.png"
              width={28}
            />
            <p className="text-sm font-semibold">Portal da Biblioteca Dumerval T.</p>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <a
              className="border border-border px-3 py-1.5 text-sm font-medium hover:border-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              href="/gestao"
            >
              Gestão
            </a>
          </div>
        </header>

        <section className="hero-modern relative isolate overflow-hidden border-b border-border py-14 text-center sm:py-20">
          <div aria-hidden="true" className="hero-glow" />
          <Image
            alt=""
            aria-hidden="true"
            className="hero-jose absolute z-[1]"
            height={500}
            loading="eager"
            sizes="(max-width: 640px) 48vw, 300px"
            src="/branding/jose-americo-atualizado.png"
            width={301}
          />
          <Image
            alt=""
            aria-hidden="true"
            className="hero-jose hero-jose-mirror absolute z-[1]"
            height={500}
            sizes="(max-width: 640px) 48vw, 300px"
            src="/branding/jose-americo-atualizado.png"
            width={301}
          />
          <div className="hero-copy relative z-10">
            <p className="piece-number mb-5">
              <strong>●</strong> Portal interno da biblioteca
            </p>
            <h1 className="hero-title mx-auto max-w-3xl font-display font-bold">
              Todos os sistemas
              <br />
              em <span className="accent">um lugar só.</span>
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-[17px]">
              Busque, inicie e abra os sistemas num lugar limpo e rápido — sem atalho perdido.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <a
                className="inline-flex items-center gap-2 bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                href="#sistemas"
              >
                Ver sistemas
                <ArrowDown aria-hidden="true" size={16} strokeWidth={2.5} />
              </a>
              <a
                className="inline-flex items-center gap-2 border border-border bg-card px-5 py-3 text-sm font-semibold text-foreground transition hover:border-foreground/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                href="#busca"
              >
                <Search aria-hidden="true" size={16} />
                Buscar
              </a>
            </div>
          </div>
        </section>

        <Catalog />

        <footer className="mt-12 border-t border-border py-5 text-xs text-muted-foreground">
          © 2026 · {" "}
          <a className="underline underline-offset-2 hover:text-foreground" href="https://portsamuellmsa.vercel.app" rel="noopener noreferrer" target="_blank">
            Samuel Lucas
          </a>
          {" · "}
          <a className="underline underline-offset-2 hover:text-foreground" href="https://miguel-fernandes-portfolio.vercel.app/" rel="noopener noreferrer" target="_blank">
            Miguel Fernandes
          </a>
        </footer>
      </div>
    </main>
  );
}
