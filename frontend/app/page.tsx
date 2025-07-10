"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Film, Play, Star, Users, Sparkles, TrendingUp, ArrowRight, Zap } from "lucide-react"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

export default function LandingPage() {
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    // Animaciones de entrada
    const tl = gsap.timeline()

    tl.fromTo(".hero-content", { opacity: 0, y: 100 }, { opacity: 1, y: 0, duration: 1.2, ease: "power3.out" })
      .fromTo(
        ".hero-buttons",
        { opacity: 0, y: 50 },
        { opacity: 1, y: 0, duration: 0.8, ease: "back.out(1.7)" },
        "-=0.5",
      )
      .fromTo(
        ".feature-card",
        { opacity: 0, scale: 0.8, y: 50 },
        { opacity: 1, scale: 1, y: 0, duration: 0.8, stagger: 0.2, ease: "back.out(1.7)" },
        "-=0.3",
      )

    // Animación de partículas flotantes
    gsap.to(".floating-particle", {
      y: -20,
      duration: 3,
      ease: "power1.inOut",
      yoyo: true,
      repeat: -1,
      stagger: 0.5,
    })

    // Scroll animations
    gsap.fromTo(
      ".stats-section",
      { opacity: 0, y: 100 },
      {
        opacity: 1,
        y: 0,
        duration: 1,
        scrollTrigger: {
          trigger: ".stats-section",
          start: "top 80%",
          end: "bottom 20%",
          toggleActions: "play none none reverse",
        },
      },
    )
  }, [])

  const handleGetStarted = () => {
    setIsLoading(true)
    gsap.to(".landing-container", {
      opacity: 0,
      scale: 0.95,
      duration: 0.6,
      onComplete: () => router.push("/register"),
    })
  }

  const handleLogin = () => {
    router.push("/login")
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 landing-container overflow-hidden">
      {/* Partículas flotantes */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="floating-particle absolute w-2 h-2 bg-purple-400/30 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
            }}
          />
        ))}
      </div>

      {/* Header */}
      <header className="relative z-10 p-6">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Film className="h-10 w-10 text-purple-400" />
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              CineAI
            </h1>
          </div>

          <Button
            variant="outline"
            onClick={handleLogin}
            className="bg-white/10 border-white/20 text-white hover:bg-white/20"
          >
            Iniciar Sesión
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 container mx-auto px-6 py-20">
        <div className="text-center hero-content">
          <div className="inline-flex items-center space-x-2 bg-purple-500/20 backdrop-blur-sm rounded-full px-4 py-2 mb-8">
            <Sparkles className="h-4 w-4 text-purple-400" />
            <span className="text-purple-300 text-sm font-medium">Powered by AI & ML32M Dataset</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Descubre tu próxima
            <span className="block bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">
              película favorita
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
            Recomendaciones inteligentes basadas en embeddings vectoriales y machine learning avanzado. Más de 32
            millones de interacciones analizadas para encontrar exactamente lo que buscas.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center hero-buttons">
            <Button
              size="lg"
              onClick={handleGetStarted}
              disabled={isLoading}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-8 py-4 text-lg group"
            >
              {isLoading ? (
                "Cargando..."
              ) : (
                <>
                  <Play className="h-5 w-5 mr-2 group-hover:scale-110 transition-transform" />
                  Comenzar Gratis
                  <ArrowRight className="h-5 w-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </Button>

            <Button
              size="lg"
              variant="outline"
              className="bg-white/10 border-white/20 text-white hover:bg-white/20 px-8 py-4 text-lg backdrop-blur-sm"
            >
              <Film className="h-5 w-5 mr-2" />
              Ver Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-10 container mx-auto px-6 py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="bg-white/10 backdrop-blur-sm border-white/20 feature-card group hover:bg-white/15 transition-all duration-300">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
                <Zap className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">IA Avanzada</h3>
              <p className="text-gray-300 leading-relaxed">
                Algoritmos de machine learning que aprenden de tus gustos y mejoran con cada interacción
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-white/20 feature-card group hover:bg-white/15 transition-all duration-300">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
                <Users className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">32M+ Interacciones</h3>
              <p className="text-gray-300 leading-relaxed">
                Dataset masivo de MovieLens con millones de calificaciones reales de usuarios
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-white/20 feature-card group hover:bg-white/15 transition-all duration-300">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
                <TrendingUp className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Búsqueda Vectorial</h3>
              <p className="text-gray-300 leading-relaxed">
                Encuentra películas similares usando embeddings vectoriales y similitud semántica
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative z-10 container mx-auto px-6 py-20 stats-section">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">Números que Impresionan</h2>
          <p className="text-xl text-gray-300">La potencia de nuestro sistema de recomendación</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="text-center">
            <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
              32M+
            </div>
            <p className="text-gray-300 font-medium">Calificaciones</p>
          </div>

          <div className="text-center">
            <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent mb-2">
              58K+
            </div>
            <p className="text-gray-300 font-medium">Películas</p>
          </div>

          <div className="text-center">
            <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent mb-2">
              280K+
            </div>
            <p className="text-gray-300 font-medium">Usuarios</p>
          </div>

          <div className="text-center">
            <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent mb-2">
              95%
            </div>
            <p className="text-gray-300 font-medium">Precisión</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 container mx-auto px-6 py-20">
        <Card className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 backdrop-blur-sm border-purple-500/30">
          <CardContent className="p-12 text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              ¿Listo para descubrir tu próxima obsesión cinematográfica?
            </h2>
            <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
              Únete a miles de usuarios que ya disfrutan de recomendaciones personalizadas con IA
            </p>
            <Button
              size="lg"
              onClick={handleGetStarted}
              disabled={isLoading}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-12 py-4 text-lg"
            >
              <Star className="h-5 w-5 mr-2" />
              Comenzar Ahora
            </Button>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <Film className="h-6 w-6 text-purple-400" />
              <span className="text-white font-semibold">CineAI</span>
              <Badge variant="secondary" className="bg-purple-500/20 text-purple-300">
                Beta
              </Badge>
            </div>
            <p className="text-gray-400 text-sm">© 2024 CineAI. Powered by ML32M Dataset & Vector Search</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
