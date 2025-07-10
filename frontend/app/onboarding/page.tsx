"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Film, Check, ArrowRight, Sparkles, TrendingUp } from "lucide-react"
import { gsap } from "gsap"
import MovieCard from "@/components/movie-card"
import { getMovieDetails } from "@/lib/tmdb-service"

interface Movie {
  movie_id: number
  title: string
  year?: number
  genres?: string
  poster_path?: string
  overview?: string
  vote_average?: number
}

interface TrendingMovies {
  [genre: string]: Movie[]
}

export default function OnboardingPage() {
  const [userId, setUserId] = useState<string>("")
  const [username, setUsername] = useState<string>("")
  const [trendingMovies, setTrendingMovies] = useState<TrendingMovies>({})
  const [selectedMovies, setSelectedMovies] = useState<{ [genre: string]: number[] }>({})
  const [activeGenre, setActiveGenre] = useState<string>("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [step, setStep] = useState(1)
  const router = useRouter()

  useEffect(() => {
    const storedUserId = localStorage.getItem("userId")
    const storedUsername = localStorage.getItem("username")

    if (!storedUserId) {
      router.push("/register")
      return
    }

    setUserId(storedUserId)
    setUsername(storedUsername || "Usuario")
    loadTrendingMovies()
  }, [router])

  useEffect(() => {
    if (!isLoading && Object.keys(trendingMovies).length > 0) {
      // Animaciones de entrada
      gsap.fromTo(".onboarding-header", { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" })

      gsap.fromTo(".genre-tabs", { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.6, delay: 0.2 })

      gsap.fromTo(
        ".movie-grid .movie-card",
        { opacity: 0, y: 50 },
        { opacity: 1, y: 0, duration: 0.6, stagger: 0.1, delay: 0.4 },
      )
    }
  }, [isLoading, trendingMovies])

  const loadTrendingMovies = async () => {
    try {
      const response = await fetch("http://localhost:8000/trending_movies?limit_per_genre=12")
      const data = await response.json()

      // Enriquecer con datos de TMDB
      const enrichedTrending: TrendingMovies = {}

      for (const [genre, movies] of Object.entries(data.trending_by_genre)) {
        const enrichedMovies = await Promise.all(
          (movies as Movie[]).map(async (movie) => {
            const tmdbData = await getMovieDetails(movie.title, movie.year)
            return { ...movie, ...tmdbData }
          }),
        )
        enrichedTrending[genre] = enrichedMovies
      }

      setTrendingMovies(enrichedTrending)

      // Establecer primer género como activo
      const firstGenre = Object.keys(enrichedTrending)[0]
      if (firstGenre) {
        setActiveGenre(firstGenre)
      }
    } catch (error) {
      console.error("Error loading trending movies:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMovieSelect = (genre: string, movieId: number) => {
    setSelectedMovies((prev) => {
      const genreMovies = prev[genre] || []
      const isSelected = genreMovies.includes(movieId)

      return {
        ...prev,
        [genre]: isSelected ? genreMovies.filter((id) => id !== movieId) : [...genreMovies, movieId],
      }
    })

    // Animación de selección
    gsap.to(`.movie-card-${movieId}`, {
      scale: 0.95,
      duration: 0.1,
      yoyo: true,
      repeat: 1,
    })
  }

  const getTotalSelected = () => {
    return Object.values(selectedMovies).reduce((total, movies) => total + movies.length, 0)
  }

  const handleContinue = async () => {
    if (getTotalSelected() < 5) {
      alert("Selecciona al menos 5 películas para continuar")
      return
    }

    setIsSubmitting(true)

    try {
      const response = await fetch("http://localhost:8000/set_preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number.parseInt(userId),
          movies_by_genre: selectedMovies,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        // Animación de éxito
        gsap.to(".onboarding-container", {
          scale: 0.9,
          opacity: 0,
          duration: 0.6,
          onComplete: () => router.push("/dashboard"),
        })
      } else {
        alert(data.detail || "Error configurando preferencias")
      }
    } catch (error) {
      console.error("Error setting preferences:", error)
      alert("Error conectando con el servidor")
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-white text-lg">Cargando películas populares...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 onboarding-container">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8 onboarding-header">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <Film className="h-10 w-10 text-purple-400" />
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              ¡Bienvenido, {username}!
            </h1>
          </div>

          <p className="text-xl text-gray-300 mb-2">
            Ayúdanos a conocer tus gustos seleccionando películas que te gusten
          </p>

          <div className="flex items-center justify-center space-x-2 text-sm text-gray-400">
            <Sparkles className="h-4 w-4" />
            <span>Selecciona al menos 5 películas para obtener mejores recomendaciones</span>
          </div>
        </div>

        {/* Progress */}
        <Card className="bg-white/10 backdrop-blur-sm border-white/20 mb-8">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <TrendingUp className="h-5 w-5 text-purple-400" />
                <span className="text-white font-medium">Progreso de Selección</span>
              </div>

              <div className="flex items-center space-x-4">
                <Badge
                  variant={getTotalSelected() >= 5 ? "default" : "outline"}
                  className={getTotalSelected() >= 5 ? "bg-green-600 text-white" : "bg-white/10 text-gray-300"}
                >
                  {getTotalSelected()} / 5 mínimo
                </Badge>

                <Button
                  onClick={handleContinue}
                  disabled={getTotalSelected() < 5 || isSubmitting}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                >
                  {isSubmitting ? "Configurando..." : "Continuar"}
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Genre Tabs */}
        <Tabs value={activeGenre} onValueChange={setActiveGenre} className="genre-tabs">
          <TabsList className="grid grid-cols-3 lg:grid-cols-6 bg-white/10 backdrop-blur-sm mb-8">
            {Object.keys(trendingMovies)
              .slice(0, 6)
              .map((genre) => (
                <TabsTrigger key={genre} value={genre} className="data-[state=active]:bg-purple-600 text-sm">
                  {genre}
                  {selectedMovies[genre]?.length > 0 && (
                    <Badge className="ml-2 bg-green-600 text-white text-xs">{selectedMovies[genre].length}</Badge>
                  )}
                </TabsTrigger>
              ))}
          </TabsList>

          {Object.entries(trendingMovies).map(([genre, movies]) => (
            <TabsContent key={genre} value={genre}>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-white mb-2">Películas de {genre}</h2>
                <p className="text-gray-400">
                  Selecciona las películas de {genre.toLowerCase()} que te gusten o hayas disfrutado
                </p>
              </div>

              <div className="movie-grid grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6">
                {movies.map((movie, index) => (
                  <div
                    key={movie.movie_id}
                    className={`movie-card relative cursor-pointer transition-all duration-300 ${
                      selectedMovies[genre]?.includes(movie.movie_id)
                        ? "ring-4 ring-purple-500 ring-opacity-75"
                        : "hover:scale-105"
                    }`}
                    onClick={() => handleMovieSelect(genre, movie.movie_id)}
                  >
                    <MovieCard movie={movie} index={index} showYear={true} />

                    {/* Selection Indicator */}
                    {selectedMovies[genre]?.includes(movie.movie_id) && (
                      <div className="absolute top-2 right-2 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center shadow-lg">
                        <Check className="h-5 w-5 text-white" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </TabsContent>
          ))}
        </Tabs>

        {/* Bottom CTA */}
        <div className="fixed bottom-0 left-0 right-0 bg-black/80 backdrop-blur-sm border-t border-white/10 p-4">
          <div className="container mx-auto flex items-center justify-between">
            <div className="text-white">
              <span className="font-medium">{getTotalSelected()} películas seleccionadas</span>
              {getTotalSelected() < 5 && (
                <span className="text-gray-400 ml-2">(Necesitas {5 - getTotalSelected()} más)</span>
              )}
            </div>

            <Button
              onClick={handleContinue}
              disabled={getTotalSelected() < 5 || isSubmitting}
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold"
            >
              {isSubmitting ? "Configurando..." : "Finalizar Configuración"}
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
