import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import logoImg from "../assets/logo.png";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err: any) {
      setError(err.detail || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div
        className="hidden lg:flex lg:w-1/2 items-center justify-center relative"
        style={{
          background: "linear-gradient(135deg, #5A0E16 0%, #7E1320 50%, #941A29 100%)",
        }}
      >
        <div className="text-center px-8 lg:px-12">
          <img
            src={logoImg}
            alt="Holy Angel University"
            className="mx-auto mb-8 object-contain"
            style={{ width: "clamp(160px, 18vw, 260px)", height: "clamp(160px, 18vw, 260px)" }}
          />
          <h1
            className="font-heading font-bold text-white mb-4 leading-tight"
            style={{ fontSize: "clamp(32px, 4.5vw, 64px)" }}
          >
            University Research Office
          </h1>
          <p
            className="text-white/80 mb-2"
            style={{ fontSize: "clamp(18px, 2.5vw, 34px)" }}
          >
            Research Monitoring System
          </p>
          <p
            className="text-white/60"
            style={{ fontSize: "clamp(15px, 2vw, 28px)" }}
          >
            Holy Angel University
          </p>
          <div
            className="mt-14 text-white/45 uppercase"
            style={{ fontSize: "clamp(13px, 1.8vw, 26px)", letterSpacing: "0.25em" }}
          >
            Virtus · Scientia · Caritas
          </div>
        </div>
      </div>

      {/* Right panel - Login form */}
      <div className="flex-1 flex items-center justify-center bg-cream-50 px-6">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <h2 className="font-heading text-3xl font-bold text-gray-800">Welcome back</h2>
            <p className="text-gray-500 mt-2 text-sm">Sign in to access the University Research Office Research Monitoring System</p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-control bg-red-50 border border-red-200 text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-control border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-maroon-500/30 focus:border-maroon-500 transition-colors"
                placeholder="you@hau.edu.ph"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-control border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-maroon-500/30 focus:border-maroon-500 transition-colors"
                placeholder="Enter your password"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-maroon-700 text-white py-3 rounded-control text-sm font-semibold hover:bg-maroon-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="text-center text-xs text-gray-400 mt-6">
            For demo credentials, contact the system administrator.
          </p>
        </div>
      </div>
    </div>
  );
}
