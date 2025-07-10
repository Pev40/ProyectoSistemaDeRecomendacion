"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Film, ArrowLeft, User, Mail, Heart, Calendar, MapPin, ArrowRight } from "lucide-react"
import { gsap } from "gsap"

interface Genre {
  id: string
  name: string
  color: string
}

const GENRE_COLORS = [
  "bg-red-500",
  "bg-blue-500",
  "bg-green-500",
  "bg-yellow-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-indigo-500",
  "bg-orange-500",
  "bg-teal-500",
  "bg-cyan-500",
  "bg-lime-500",
  "bg-rose-500",
  "bg-violet-500",
  "bg-amber-500",
  "bg-emerald-500",
  "bg-sky-500",
  "bg-fuchsia-500",
  "bg-slate-500",
]

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    preferred_genres: [] as string[],
    age_range: "",
    country: "",
  })
  const [availableGenres, setAvailableGenres] = useState<Genre[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [step, setStep] = useState(1)
  const router = useRouter()

  useEffect(() => {
    loadGenres()

    // Animaciones de entrada
    gsap.fromTo(
      ".register-container",
      { opacity: 0, scale: 0.9 },
      { opacity: 1, scale: 1, duration: 0.8, ease: "back.out(1.7)" },
    )
  }, [])

  const loadGenres = async () => {
    try {
      const response = await fetch("http://localhost:8000/genres")
      const data = await response.json()

      const genresWithColors = data.genres.map((genre: string, index: number) => ({
        id: genre,
        name: genre,
        color: GENRE_COLORS[index % GENRE_COLORS.length],
      }))

      setAvailableGenres(genresWithColors)
    } catch (error) {
      console.error("Error loading genres:", error)
    }
  }

  const handleGenreToggle = (genreId: string) => {
    setFormData((prev) => ({
      ...prev,
      preferred_genres: prev.preferred_genres.includes(genreId)
        ? prev.preferred_genres.filter((g) => g !== genreId)
        : [...prev.preferred_genres, genreId],
    }))
  }

  const handleNextStep = () => {
    if (step === 1) {
      if (!formData.username || !formData.email) {
        alert("Por favor completa todos los campos")
        return
      }

      gsap.to(".step-1", {
        x: -100,
        opacity: 0,
        duration: 0.5,
        onComplete: () => {
          setStep(2)
          gsap.fromTo(".step-2", { x: 100, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5 })
        },
      })
    }
  }

  const handlePrevStep = () => {
    gsap.to(".step-2", {
      x: 100,
      opacity: 0,
      duration: 0.5,
      onComplete: () => {
        setStep(1)
        gsap.fromTo(".step-1", { x: -100, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5 })
      },
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (formData.preferred_genres.length === 0) {
      alert("Selecciona al menos un género")
      return
    }

    if (!formData.age_range) {
      alert("Selecciona tu rango de edad")
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8000/register_user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (response.ok) {
        localStorage.setItem("userId", data.user_id.toString())
        localStorage.setItem("username", data.username)

        // Animación de éxito
        gsap.to(".register-container", {
          scale: 0.9,
          opacity: 0,
          duration: 0.6,
          onComplete: () => router.push("/onboarding"),
        })
      } else {
        alert(data.detail || "Error en el registro")
      }
    } catch (error) {
      console.error("Error registering user:", error)
      alert("Error conectando con el servidor")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl register-container">
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

        {/* Progress */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center space-x-4">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? "bg-purple-600 text-white" : "bg-gray-600 text-gray-400"}`}
            >
              1
            </div>
            <div className={`w-16 h-1 ${step >= 2 ? "bg-purple-600" : "bg-gray-600"}`} />
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? "bg-purple-600 text-white" : "bg-gray-600 text-gray-400"}`}
            >
              2
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <Card className="bg-white/10 backdrop-blur-sm border-white/20 step-1">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-bold text-white">Información Básica</CardTitle>
                <CardDescription className="text-gray-300">
                  Cuéntanos un poco sobre ti para personalizar tu experiencia
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-white flex items-center">
                    <User className="h-4 w-4 mr-2" />
                    Nombre de Usuario
                  </Label>
                  <Input
                    id="username"
                    placeholder="Tu nombre de usuario"
                    value={formData.username}
                    onChange={(e) => setFormData((prev) => ({ ...prev, username: e.target.value }))}
                    className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-white flex items-center">
                    <Mail className="h-4 w-4 mr-2" />
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="tu@email.com"
                    value={formData.email}
                    onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
                    className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-white flex items-center">
                    <Calendar className="h-4 w-4 mr-2" />
                    Rango de Edad
                  </Label>
                  <Select
                    value={formData.age_range}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, age_range: value }))}
                  >
                    <SelectTrigger className="bg-white/10 border-white/20 text-white">
                      <SelectValue placeholder="Selecciona tu rango de edad" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="teen">13-17 años</SelectItem>
                      <SelectItem value="young_adult">18-25 años</SelectItem>
                      <SelectItem value="adult">26-45 años</SelectItem>
                      <SelectItem value="senior">46+ años</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="country" className="text-white flex items-center">
                    <MapPin className="h-4 w-4 mr-2" />
                    País (Opcional)
                  </Label>
                  <Input
                    id="country"
                    placeholder="Tu país"
                    value={formData.country}
                    onChange={(e) => setFormData((prev) => ({ ...prev, country: e.target.value }))}
                    className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                  />
                </div>

                <Button
                  type="button"
                  onClick={handleNextStep}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3"
                >
                  Continuar
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Step 2: Genre Preferences */}
          {step === 2 && (
            <Card className="bg-white/10 backdrop-blur-sm border-white/20 step-2">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-bold text-white">Géneros Favoritos</CardTitle>
                <CardDescription className="text-gray-300">
                  Selecciona los géneros que más te gustan (mínimo 1, máximo 10)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {availableGenres.map((genre) => (
                    <div
                      key={genre.id}
                      className={`relative cursor-pointer transition-all duration-300 ${
                        formData.preferred_genres.includes(genre.id) ? "scale-105" : "hover:scale-102"
                      }`}
                      onClick={() => handleGenreToggle(genre.id)}
                    >
                      <Badge
                        variant={formData.preferred_genres.includes(genre.id) ? "default" : "outline"}
                        className={`w-full justify-center py-3 px-4 text-sm font-medium transition-all ${
                          formData.preferred_genres.includes(genre.id)
                            ? `${genre.color} text-white border-transparent shadow-lg`
                            : "bg-white/10 text-gray-300 border-white/20 hover:bg-white/20"
                        }`}
                      >
                        <Heart
                          className={`h-4 w-4 mr-2 ${formData.preferred_genres.includes(genre.id) ? "fill-current" : ""}`}
                        />
                        {genre.name}
                      </Badge>
                    </div>
                  ))}
                </div>

                <div className="text-center text-sm text-gray-400">
                  {formData.preferred_genres.length} de 10 géneros seleccionados
                </div>

                <div className="flex space-x-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handlePrevStep}
                    className="flex-1 bg-white/10 border-white/20 text-white hover:bg-white/20"
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Anterior
                  </Button>

                  <Button
                    type="submit"
                    disabled={isLoading || formData.preferred_genres.length === 0}
                    className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold"
                  >
                    {isLoading ? "Registrando..." : "Crear Cuenta"}
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </form>
      </div>
    </div>
  )
}
