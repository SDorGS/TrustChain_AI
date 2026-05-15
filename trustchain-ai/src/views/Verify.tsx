import { useState, FormEvent, ChangeEvent } from "react";
import { Camera, Package, ShieldCheck, Sparkles, Tag } from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { runVerification } from "../api/client";

const REPORT_STORAGE_KEY = "trustchain_latest_report";

export default function Verify() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [image, setImage] = useState<File | null>(null);
  const [productData, setProductData] = useState({
    name: "",
    batch: "",
    nafdac: "",
    vendor: "",
    price: "",
  });

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setProductData({ ...productData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setImage(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!image) {
      alert("Please upload a product image first.");
      return;
    }

    if (!productData.price || Number.isNaN(Number(productData.price))) {
      alert("Please enter a valid product price.");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("product_name", productData.name);
    formData.append("batch_no", productData.batch);
    formData.append("nafdac_no", productData.nafdac);
    formData.append("price", productData.price);
    formData.append("vendor_name", productData.vendor);
    formData.append("image", image);

    try {
      const result = await runVerification(formData);

      sessionStorage.setItem(REPORT_STORAGE_KEY, JSON.stringify(result));
      navigate("/result", { state: { data: result } });
    } catch (error) {
      console.error("Verification failed", error);
      alert("Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto w-full px-4 md:px-12 py-12">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-on-surface mb-2">Forensic Intelligence</h1>
        <p className="text-on-surface-variant">Enter the product details, then run verification.</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
          <section className="glass-panel p-8 rounded-2xl border border-on-surface/10">
            <div className="flex items-center gap-3 mb-10 text-on-surface">
              <Package />
              <h2 className="text-2xl font-bold">Product Registry</h2>
            </div>

            <div className="group border-2 border-dashed border-on-surface/10 rounded-2xl p-16 flex flex-col items-center justify-center bg-surface-container-low relative">
              <input
                type="file"
                accept="image/png,image/jpeg"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Camera size={48} className="text-on-surface-variant mb-4" />
              <p className="text-sm font-bold text-on-surface">
                {image ? image.name : "Upload Product Image"}
              </p>
            </div>

            <div className="mt-8 space-y-6">
              <input
                name="name"
                onChange={handleInputChange}
                value={productData.name}
                placeholder="Product Name"
                className="w-full h-12 px-4 rounded-xl border border-on-surface/10 bg-white outline-none"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  name="batch"
                  onChange={handleInputChange}
                  value={productData.batch}
                  placeholder="Batch No"
                  className="w-full h-12 px-4 rounded-xl border border-on-surface/10 bg-white outline-none"
                />
                <input
                  name="nafdac"
                  onChange={handleInputChange}
                  value={productData.nafdac}
                  placeholder="NAFDAC No"
                  className="w-full h-12 px-4 rounded-xl border border-on-surface/10 bg-white outline-none"
                />
              </div>

              <div className="relative">
                <Tag
                  size={16}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
                />
                <input
                  name="price"
                  type="number"
                  min="0"
                  onChange={handleInputChange}
                  value={productData.price}
                  placeholder="Product Price (₦)"
                  className="w-full h-12 pl-10 pr-4 rounded-xl border border-on-surface/10 bg-white outline-none"
                />
              </div>
            </div>
          </section>

          <section className="glass-panel p-8 rounded-2xl border border-on-surface/10">
            <div className="flex items-center gap-3 mb-10 text-secondary">
              <ShieldCheck />
              <h2 className="text-2xl font-bold text-on-surface">Vendor Intelligence</h2>
            </div>

            <input
              name="vendor"
              onChange={handleInputChange}
              value={productData.vendor}
              placeholder="Vendor/Business Name"
              className="w-full h-12 px-4 rounded-xl border border-on-surface/10 bg-white outline-none"
            />
          </section>
        </div>

        <div className="flex flex-col items-center gap-6">
          <motion.button
            type="submit"
            whileTap={{ scale: 0.97 }}
            disabled={loading}
            className="bg-on-tertiary-container text-white px-12 h-14 rounded-xl font-bold flex items-center gap-3 shadow-xl disabled:opacity-60"
          >
            <Sparkles size={20} />
            {loading ? "Analyzing Neural Data..." : "Run AI Verification"}
          </motion.button>
        </div>
      </form>
    </div>
  );
}