import { useLocation, useNavigate } from "react-router-dom";
import {
  ShieldCheck,
  AlertTriangle,
  ArrowLeft,
  CreditCard,
} from "lucide-react";

import { useMemo, useState } from "react";
import axios from "axios";

const REPORT_STORAGE_KEY = "trustchain_latest_report";

type Analysis = {
  score: number;
  level: string;
  flags: string[];
  verdict: string;
};

type Report = {
  id: string;
  verification_id: number;

  payment_allowed?: boolean;
  payment_status?: string;

  payment_amount?: number;
  payment_amount_kobo?: number;

  currency?: string;

  product?: {
    name?: string;
    batch_no?: string;
    nafdac_no?: string;
    price?: number;
    ocr_text?: string;
  };

  vendor?: {
    name?: string;
  };

  analysis: Analysis;
};

export default function Result() {
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const report: Report | null = useMemo(() => {
    const fromRoute = (
      location.state as { data?: Report } | null
    )?.data;

    if (fromRoute) return fromRoute;

    const stored = sessionStorage.getItem(
      REPORT_STORAGE_KEY
    );

    if (!stored) return null;

    try {
      return JSON.parse(stored) as Report;
    } catch {
      return null;
    }
  }, [location.state]);

  if (!report) {
    return (
      <div className="max-w-3xl mx-auto px-4 md:px-12 py-12">
        <div className="bg-white rounded-3xl p-8 border border-on-surface/10 shadow-sm">

          <p className="text-lg font-semibold text-on-surface mb-3">
            No verification data found.
          </p>

          <p className="text-on-surface-variant">
            Run a verification first.
          </p>

          <button
            onClick={() => navigate("/verify")}
            className="mt-6 px-4 py-2 bg-secondary text-white rounded-lg"
          >
            Go Back
          </button>

        </div>
      </div>
    );
  }

  const analysis = report.analysis;

  const flags = Array.isArray(analysis.flags)
    ? analysis.flags
    : [];

  const paymentAmount =
    report.payment_amount ??
    report.product?.price ??
    0;

  const paymentAllowed =
    report.payment_allowed ?? false;

  const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ??
    "http://localhost:8000/api/v1";

  const handlePayment = async () => {

    if (!paymentAllowed) {
      return;
    }

    try {

      setLoading(true);
      setError("");

      const payload = {
        email: "test@example.com",

        // IMPORTANT:
        // actual vendor payment
        amount: paymentAmount,

        verification_id:
          report.verification_id,
      };

      const response = await axios.post(
        `${API_BASE_URL}/payments/initiate`,
        payload
      );

      const checkoutUrl =
        response.data?.data?.checkout_url ??
        response.data?.data?.checkoutUrl;

      if (checkoutUrl) {
        window.location.href = checkoutUrl;
      } else {
        setError(
          "Unable to initialize payment."
        );
      }

    } catch (err) {

      console.error(err);

      setError(
        "Payment initiation failed."
      );

    } finally {

      setLoading(false);

    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 md:px-12 py-12">

      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 mb-8 text-sm font-semibold"
      >
        <ArrowLeft size={18} />
        Back
      </button>

      <div className="bg-white rounded-3xl p-8 border border-on-surface/10 shadow-sm">

        <div className="flex items-center gap-4 mb-8">

          {analysis.level === "HIGH" ? (
            <AlertTriangle
              className="text-error"
              size={40}
            />
          ) : (
            <ShieldCheck
              className="text-on-tertiary-container"
              size={40}
            />
          )}

          <div>
            <h1 className="text-3xl font-bold">
              Trust Score: {analysis.score}%
            </h1>

            <p className="text-on-surface-variant">
              {analysis.verdict}
            </p>
          </div>

        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">

          <div className="p-4 rounded-xl bg-surface-container-low">

            <p className="text-xs uppercase tracking-widest text-on-surface-variant mb-1">
              Product
            </p>

            <p className="font-semibold text-on-surface">
              {report.product?.name ?? "Unknown"}
            </p>

          </div>

          <div className="p-4 rounded-xl bg-surface-container-low">

            <p className="text-xs uppercase tracking-widest text-on-surface-variant mb-1">
              Price
            </p>

            <p className="font-semibold text-on-surface">
              ₦{paymentAmount}
            </p>

          </div>

          <div className="p-4 rounded-xl bg-surface-container-low">

            <p className="text-xs uppercase tracking-widest text-on-surface-variant mb-1">
              Payment
            </p>

            <p className="font-semibold text-on-surface">

              {paymentAllowed
                ? "Allowed"
                : "Paused"}

            </p>

          </div>

        </div>

        {flags.length > 0 && (

          <div className="mb-8">

            <h2 className="text-lg font-semibold mb-4">
              Risk Flags
            </h2>

            <div className="space-y-3">

              {flags.map((flag, index) => (

                <div
                  key={index}
                  className="flex items-center gap-3 p-3 rounded-xl bg-error/5 text-error"
                >
                  <AlertTriangle size={18} />
                  <span>{flag}</span>
                </div>

              ))}

            </div>

          </div>

        )}

        {error && (
          <div className="mb-6 text-error font-medium">
            {error}
          </div>
        )}

        <div className="flex justify-end">

          {paymentAllowed ? (

            <button
              onClick={handlePayment}
              disabled={loading}
              className="flex items-center gap-2 bg-secondary text-white px-6 py-3 rounded-xl font-semibold disabled:opacity-60"
            >
              <CreditCard size={18} />

              {loading
                ? "Processing..."
                : `Pay ₦${paymentAmount}`}

            </button>

          ) : (

            <button
              disabled
              className="flex items-center gap-2 bg-gray-300 text-gray-600 px-6 py-3 rounded-xl font-semibold cursor-not-allowed"
            >
              <AlertTriangle size={18} />
              Payment Paused
            </button>

          )}

        </div>

      </div>
    </div>
  );
}