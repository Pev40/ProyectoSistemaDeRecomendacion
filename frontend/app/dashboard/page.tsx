"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Film, Star, TrendingUp, User, LogOut, Search, Sparkles } from "lucide-react"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import MovieCard from "@/components/movie-card"
import { getMovieDetails } from "@/lib/tmdb-service"

gsap.registerPlugin(ScrollTrigger)

interface Movie {
  movie_id: number
  title: string
  year?: number
  full_genres?: string
  score?: number
  poster_path?: string
  overview?: string
  vote_average?: number
}

interface UserStats {
  total_ratings: number
  avg_rating: number
  favorite_genres: string[]
  total_movies: number
}

export default function Dashboard() {
  const [userId, setUserId] = useState<string>("")
  const [recommendations, setRecommendations] = useState<Movie[]>([])
  const [userStats, setUserStats] = useState<UserStats | null>(null)
  const [popularMovies, setPopularMovies] = useState<Movie[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const storedUserId = localStorage.getItem("userId")
    if (!storedUserId) {
      router.push("/")
      return
    }
    setUserId(storedUserId)
    loadDashboardData(storedUserId)
  }, [router])

  useEffect(() => {
    if (!isLoading) {
      // Animaciones de entrada
      gsap.fromTo(".dashboard-header", { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" })

      gsap.fromTo(
        ".stats-card",
        { opacity: 0, scale: 0.9 },
        { opacity: 1, scale: 1, duration: 0.6, stagger: 0.1, delay: 0.2 },
      )

      gsap.fromTo(
        ".movie-section",
        { opacity: 0, y: 50 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          stagger: 0.3,
          scrollTrigger: {
            trigger: ".movie-section",
            start: "top 80%",
            end: "bottom 20%",
            toggleActions: "play none none reverse",
          },
        },
      )
    }
  }, [isLoading])

  const loadDashboardData = async (userId: string) => {
    try {
      setIsLoading(true)

      // Cargar datos en paralelo
      const [recommendationsRes, statsRes, popularRes] = await Promise.all([
        fetch(`http://localhost:8000/recommend`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: Number.parseInt(userId), k: 12 }),
        }),
        fetch(`http://localhost:8000/user_stats/${userId}`),
        fetch(`http://localhost:8000/popular_movies?limit=8`),
      ])

      const [recommendationsData, statsData, popularData] = await Promise.all([
        recommendationsRes.json(),
        statsRes.json(),
        popularRes.json(),
      ])

      // Enriquecer recomendaciones con datos de TMDB
      const enrichedRecommendations = await Promise.all(
        recommendationsData.recommendations?.map(async (movie: Movie) => {
          const tmdbData = await getMovieDetails(movie.title, movie.year)
          return { ...movie, ...tmdbData }
        }) || [],
      )

      // Enriquecer películas populares
      const enrichedPopular = await Promise.all(
        popularData.popular_movies?.map(async (movie: Movie) => {
          const tmdbData = await getMovieDetails(movie.title, movie.year)
          return { ...movie, ...tmdbData }
        }) || [],
      )

      setRecommendations(enrichedRecommendations)
      setUserStats(statsData.stats)
      setPopularMovies(enrichedPopular)
    } catch (error) {
      console.error("Error loading dashboard data:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    gsap.to(".dashboard-container", {
      opacity: 0,
      scale: 0.9,
      duration: 0.5,
      onComplete: () => {
        localStorage.removeItem("userId")
        router.push("/")
      },
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="container mx-auto px-4 py-8">
          <div className="flex justify-between items-center mb-8">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-10 w-24" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <Skeleton key={i} className="h-80" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 dashboard-container">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 dashboard-header">
          <div className="flex items-center space-x-3 mb-4 sm:mb-0">
            <Film className="h-8 w-8 text-purple-400" />
            <div>
              <h1 className="text-3xl font-bold text-white">Bienvenido, Usuario {userId}</h1>
              <p className="text-gray-400">Descubre tu próxima película favorita</p>
            </div>
          </div>

          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={() => router.push("/movies")}
              className="bg-white/10 border-white/20 text-white hover:bg-white/20"
            >
              <Search className="h-4 w-4 mr-2" />
              Explorar
            </Button>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="bg-red-500/20 border-red-500/30 text-red-300 hover:bg-red-500/30"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Salir
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {userStats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="bg-white/10 backdrop-blur-sm border-white/20 stats-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Películas Vistas</p>
                    <p className="text-2xl font-bold text-white">{userStats.total_ratings}</p>
                  </div>
                  <Film className="h-8 w-8 text-blue-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-sm border-white/20 stats-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Rating Promedio</p>
                    <p className="text-2xl font-bold text-white">{userStats.avg_rating?.toFixed(1)}</p>
                  </div>
                  <Star className="h-8 w-8 text-yellow-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-sm border-white/20 stats-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Géneros Favoritos</p>
                    <p className="text-lg font-bold text-white">{userStats.favorite_genres?.length || 0}</p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-sm border-white/20 stats-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Perfil</p>
                    <p className="text-lg font-bold text-white">Activo</p>
                  </div>
                  <User className="h-8 w-8 text-purple-400" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Recomendaciones Personalizadas */}
        <div className="mb-12 movie-section">
          <div className="flex items-center space-x-3 mb-6">
            <Sparkles className="h-6 w-6 text-purple-400" />
            <h2 className="text-2xl font-bold text-white">Recomendaciones para Ti</h2>
            <Badge variant="secondary" className="bg-purple-500/20 text-purple-300">
              IA Personalizada
            </Badge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-6">
            {recommendations.map((movie, index) => (
              <MovieCard key={movie.movie_id} movie={movie} index={index} showScore={true} />
            ))}
          </div>
        </div>

        {/* Películas Populares */}
        <div className="movie-section">
          <div className="flex items-center space-x-3 mb-6">
            <TrendingUp className="h-6 w-6 text-orange-400" />
            <h2 className="text-2xl font-bold text-white">Tendencias Populares</h2>
            <Badge variant="secondary" className="bg-orange-500/20 text-orange-300">
              Más Vistas
            </Badge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {popularMovies.map((movie, index) => (
              <MovieCard key={movie.movie_id} movie={movie} index={index} showRating={true} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
