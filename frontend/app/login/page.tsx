"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Film, ArrowLeft, User, LogIn } from "lucide-react"
import { gsap } from "gsap"

export default function LoginPage() {
  const [userId, setUserId] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    // Animación de entrada
    gsap.fromTo(
      ".login-card",
      { opacity: 0, y: 50, scale: 0.9 },
      { opacity: 1, y: 0, scale: 1, duration: 0.8, ease: "back.out(1.7)" },
    )
  }, [])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId.trim()) return

    setIsLoading(true)

    try {
      const response = await fetch(`http://localhost:8000/user_stats/${userId}`)
      if (response.ok) {
        localStorage.setItem("userId", userId)

        // Animación de salida
        gsap.to(".login-container", {
          opacity: 0,
          scale: 0.9,
          duration: 0.5,
          onComplete: () => router.push("/dashboard"),
        })
      } else {
        alert("Usuario no encontrado. Intenta con un ID válido o regístrate.")
      }
    } catch (error) {
      console.error("Error validating user:", error)
      alert("Error conectando con el servidor")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4 login-container">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Button variant="ghost" onClick={() => router.push("/")} className="text-white hover:bg-white/10">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver
          </Button>

          <div className="flex items-center space-x-3">
            <Film className="h-8 w-8 text-purple-400" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              CineAI
            </h1>
          </div>
        </div>

        {/* Login Form */}
        <Card className="bg-white/10 backdrop-blur-sm border-white/20 shadow-2xl login-card">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-white">Iniciar Sesión</CardTitle>
            <CardDescription className="text-gray-300">
              Ingresa tu ID de usuario para acceder a tus recomendaciones
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="userId" className="text-white flex items-center">
                  <User className="h-4 w-4 mr-2" />
                  ID de Usuario
                </Label>
                <Input
                  id="userId"
                  type="number"
                  placeholder="Ej: 1, 123, 456..."
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="bg-white/10 border-white/20 text-white placeholder-gray-400 text-lg"
                  required
                />
                <p className="text-sm text-gray-400">
                  Usa cualquier ID entre 1 y 162,541 o tu ID de usuario registrado
                </p>
              </div>

              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 text-lg"
                disabled={isLoading}
              >
                {isLoading ? (
                  "Validando..."
                ) : (
                  <>
                    <LogIn className="h-5 w-5 mr-2" />
                    Entrar a CineAI
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-400 text-sm mb-3">¿No tienes cuenta?</p>
              <Button
                variant="outline"
                onClick={() => router.push("/register")}
                className="w-full bg-white/10 border-white/20 text-white hover:bg-white/20"
              >
                Crear Cuenta Nueva
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
