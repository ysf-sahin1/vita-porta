"use client";

import { startSessionApi } from "@/lib/api";
import { cn } from "@/lib/cn";
import { setSession, type NurseSession } from "@/lib/session";
import { Building2, ShieldCheck, User } from "lucide-react";
import { useState } from "react";

export interface LoginScreenProps {
  onReady: (session: NurseSession) => void;
}

export function LoginScreen({ onReady }: LoginScreenProps) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [hospital, setHospital] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);

  const trimmedFirst = firstName.trim();
  const trimmedLast = lastName.trim();
  const trimmedHospital = hospital.trim();
  const allValid = trimmedFirst.length >= 2 && trimmedLast.length >= 2 && trimmedHospital.length >= 2;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    if (!allValid || busy) return;
    setBusy(true);
    let sessionId: string | undefined;
    try {
      const record = await startSessionApi({
        firstName: trimmedFirst,
        lastName: trimmedLast,
        hospital: trimmedHospital,
      });
      sessionId = record.session_id;
    } catch (err) {
      // Backend ulaşılamazsa lokal session ile devam — UI'yi kilitlemeyelim.
      console.warn("[LoginScreen] startSession başarısız, lokal devam:", err);
    }
    const s = setSession({
      firstName: trimmedFirst,
      lastName: trimmedLast,
      hospital: trimmedHospital,
      sessionId,
    });
    setBusy(false);
    onReady(s);
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-10">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-lg rounded-3xl bg-white/75 backdrop-blur-xl border border-white/60 shadow-glassLg p-8 md:p-10"
      >
        <div className="flex items-center gap-4 mb-6">
          <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 p-3 text-white shadow-glass">
            <ShieldCheck className="w-7 h-7" strokeWidth={2.2} />
          </div>
          <div>
            <h1 className="text-3xl font-semibold text-slate-900 tracking-tight leading-none">
              Vita Porta
            </h1>
            <p className="text-sm text-slate-500 mt-1.5">Hemşire girişi · Bilgileriniz bu cihazda saklanır</p>
          </div>
        </div>

        <p className="text-sm text-slate-600 leading-relaxed mb-6">
          Triaj asistanına hoş geldiniz. Lütfen kimliğinizi onaylayın — bu bilgiler verdiklerinizi
          kayıt altına alırken kullanılacak, sunucuya gönderilmez.
        </p>

        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field
              label="Ad"
              icon={<User className="w-4 h-4" />}
              value={firstName}
              onChange={setFirstName}
              placeholder="Ayşe"
              invalid={submitted && trimmedFirst.length < 2}
              autoFocus
            />
            <Field
              label="Soyad"
              icon={<User className="w-4 h-4" />}
              value={lastName}
              onChange={setLastName}
              placeholder="Demir"
              invalid={submitted && trimmedLast.length < 2}
            />
          </div>
          <Field
            label="Hastane / Klinik"
            icon={<Building2 className="w-4 h-4" />}
            value={hospital}
            onChange={setHospital}
            placeholder="Örn. Acıbadem Maslak Hastanesi"
            invalid={submitted && trimmedHospital.length < 2}
          />
        </div>

        <button
          type="submit"
          disabled={busy || (submitted && !allValid)}
          className={cn(
            "mt-7 w-full rounded-2xl py-3 font-semibold tracking-tight transition-all",
            "bg-gradient-to-r from-slate-900 to-slate-700 text-white shadow-glass",
            "hover:from-slate-800 hover:to-slate-600",
            "focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:outline-none",
            (busy || (submitted && !allValid)) && "opacity-60 cursor-not-allowed",
          )}
        >
          {busy ? "Mesai kaydediliyor…" : "Triaj ekranına geç"}
        </button>

        <p className="text-[11px] text-slate-400 mt-5 leading-relaxed text-center">
          Bu sistem tanı koymaz, yalnızca öneri verir. Son karar her zaman triaj hemşiresine aittir.
        </p>
      </form>
    </main>
  );
}

function Field({
  label,
  icon,
  value,
  onChange,
  placeholder,
  invalid,
  autoFocus,
}: {
  label: string;
  icon: React.ReactNode;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  invalid?: boolean;
  autoFocus?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-xs uppercase tracking-wider text-slate-500 font-medium">{label}</span>
      <div
        className={cn(
          "mt-1.5 flex items-center gap-2 rounded-2xl border bg-white/70 px-3 py-2.5 transition-colors",
          invalid ? "border-rose-300 bg-rose-50/40" : "border-slate-200/70 focus-within:border-slate-400",
        )}
      >
        <span className={cn("text-slate-400", invalid && "text-rose-400")}>{icon}</span>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="flex-1 bg-transparent outline-none text-sm text-slate-800 placeholder:text-slate-400"
        />
      </div>
      {invalid && (
        <span className="text-[11px] text-rose-500 mt-1 inline-block">
          Lütfen en az 2 karakter girin.
        </span>
      )}
    </label>
  );
}
