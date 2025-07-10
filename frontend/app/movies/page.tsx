"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Film, Search, ArrowLeft, Filter, Star, Calendar } from "lucide-react"
import { gsap } from "gsap"
import MovieCard from "@/components/movie-card"
import { getMovieDetails } from "@/lib/tmdb-service"

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

export default function MoviesPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<Movie[]>([])
  const [popularMovies, setPopularMovies] = useState<Movie[]>([])
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null)
  const [similarMovies, setSimilarMovies] = useState<Movie[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("search")
  const router = useRouter()

  useEffect(() => {
    // Verificar autenticación
    const userId = localStorage.getItem("userId")
    if (!userId) {
      router.push("/")
      return
    }

    // Cargar películas populares al inicio
    loadPopularMovies()

    // Animaciones de entrada
    gsap.fromTo(".movies-header", { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" })
  }, [router])

  const loadPopularMovies = async () => {
    try {
      const response = await fetch("http://localhost:8000/popular_movies?limit=20")
      const data = await response.json()

      const enrichedMovies = await Promise.all(
        data.popular_movies?.map(async (movie: Movie) => {
          const tmdbData = await getMovieDetails(movie.title, movie.year)
          return { ...movie, ...tmdbData }
        }) || [],
      )

      setPopularMovies(enrichedMovies)
    } catch (error) {
      console.error("Error loading popular movies:", error)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setIsLoading(true)
    try {
      const response = await fetch("http://localhost:8000/search_movies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, limit: 20 }),
      })

      const data = await response.json()

      const enrichedResults = await Promise.all(
        data.results?.map(async (movie: Movie) => {
          const tmdbData = await getMovieDetails(movie.title, movie.year)
          return { ...movie, ...tmdbData }
        }) || [],
      )

      setSearchResults(enrichedResults)

      // Animar resultados
      gsap.fromTo(
        ".search-results .movie-card",
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, duration: 0.6, stagger: 0.1 },
      )
    } catch (error) {
      console.error("Error searching movies:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMovieSelect = async (movie: Movie) => {
    setSelectedMovie(movie)
    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8000/similar_movies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ movie_id: movie.movie_id, k: 12 }),
      })

      const data = await response.json()

      const enrichedSimilar = await Promise.all(
        data.similar_movies?.map(async (movie: Movie) => {
          const tmdbData = await getMovieDetails(movie.title, movie.year)
          return { ...movie, ...tmdbData }
        }) || [],
      )

      setSimilarMovies(enrichedSimilar)
      setActiveTab("similar")

      // Animar transición
      gsap.fromTo(
        ".similar-section",
        { opacity: 0, scale: 0.95 },
        { opacity: 1, scale: 1, duration: 0.8, ease: "back.out(1.7)" },
      )
    } catch (error) {
      console.error("Error loading similar movies:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 movies-header">
          <div className="flex items-center space-x-3 mb-4 sm:mb-0">
            <Button
              variant="ghost"
              onClick={() => router.push("/dashboard")}
              className="text-white hover:bg-white/10 p-2"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <Film className="h-8 w-8 text-purple-400" />
            <div>
              <h1 className="text-3xl font-bold text-white">Explorar Películas</h1>
              <p className="text-gray-400">Busca y descubre nuevas películas</p>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <Card className="bg-white/10 backdrop-blur-sm border-white/20 mb-8">
          <CardContent className="p-6">
            <form onSubmit={handleSearch} className="flex space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <Input
                  placeholder="Buscar películas por título..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-white/10 border-white/20 text-white placeholder-gray-400"
                />
              </div>
              <Button type="submit" disabled={isLoading} className="bg-purple-600 hover:bg-purple-700">
                {isLoading ? "Buscando..." : "Buscar"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-white/10 backdrop-blur-sm">
            <TabsTrigger value="search" className="data-[state=active]:bg-purple-600">
              <Search className="h-4 w-4 mr-2" />
              Búsqueda
            </TabsTrigger>
            <TabsTrigger value="popular" className="data-[state=active]:bg-purple-600">
              <Star className="h-4 w-4 mr-2" />
              Populares
            </TabsTrigger>
            <TabsTrigger value="similar" className="data-[state=active]:bg-purple-600">
              <Filter className="h-4 w-4 mr-2" />
              Similares
            </TabsTrigger>
          </TabsList>

          {/* Search Results */}
          <TabsContent value="search" className="mt-8">
            {searchResults.length > 0 ? (
              <div className="search-results">
                <div className="flex items-center space-x-3 mb-6">
                  <h2 className="text-2xl font-bold text-white">Resultados de Búsqueda</h2>
                  <Badge variant="secondary" className="bg-blue-500/20 text-blue-300">
                    {searchResults.length} encontradas
                  </Badge>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                  {searchResults.map((movie, index) => (
                    <MovieCard
                      key={movie.movie_id}
                      movie={movie}
                      index={index}
                      onClick={() => handleMovieSelect(movie)}
                      showYear={true}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <Search className="h-16 w-16 text-gray-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-400 mb-2">
                  {searchQuery ? "No se encontraron resultados" : "Busca películas por título"}
                </h3>
                <p className="text-gray-500">
                  {searchQuery
                    ? "Intenta con otro término de búsqueda"
                    : "Escribe el nombre de una película para comenzar"}
                </p>
              </div>
            )}
          </TabsContent>

          {/* Popular Movies */}
          <TabsContent value="popular" className="mt-8">
            <div className="flex items-center space-x-3 mb-6">
              <h2 className="text-2xl font-bold text-white">Películas Populares</h2>
              <Badge variant="secondary" className="bg-orange-500/20 text-orange-300">
                Más Vistas
              </Badge>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {popularMovies.map((movie, index) => (
                <MovieCard
                  key={movie.movie_id}
                  movie={movie}
                  index={index}
                  onClick={() => handleMovieSelect(movie)}
                  showRating={true}
                />
              ))}
            </div>
          </TabsContent>

          {/* Similar Movies */}
          <TabsContent value="similar" className="mt-8">
            {selectedMovie ? (
              <div className="similar-section">
                {/* Selected Movie Info */}
                <Card className="bg-white/10 backdrop-blur-sm border-white/20 mb-8">
                  <CardContent className="p-6">
                    <div className="flex items-start space-x-6">
                      {selectedMovie.poster_path && (
                        <img
                          src={`https://image.tmdb.org/t/p/w200${selectedMovie.poster_path}`}
                          alt={selectedMovie.title}
                          className="w-24 h-36 object-cover rounded-lg"
                        />
                      )}
                      <div className="flex-1">
                        <h3 className="text-2xl font-bold text-white mb-2">{selectedMovie.title}</h3>
                        {selectedMovie.year && (
                          <div className="flex items-center space-x-2 mb-2">
                            <Calendar className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-400">{selectedMovie.year}</span>
                          </div>
                        )}
                        {selectedMovie.full_genres && (
                          <div className="flex flex-wrap gap-2 mb-3">
                            {selectedMovie.full_genres.split("|").map((genre, i) => (
                              <Badge key={i} variant="outline" className="border-purple-400 text-purple-300">
                                {genre}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {selectedMovie.overview && (
                          <p className="text-gray-300 text-sm leading-relaxed">{selectedMovie.overview}</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Similar Movies */}
                <div className="flex items-center space-x-3 mb-6">
                  <h2 className="text-2xl font-bold text-white">Películas Similares</h2>
                  <Badge variant="secondary" className="bg-green-500/20 text-green-300">
                    IA Vectorial
                  </Badge>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-6">
                  {similarMovies.map((movie, index) => (
                    <MovieCard
                      key={movie.movie_id}
                      movie={movie}
                      index={index}
                      onClick={() => handleMovieSelect(movie)}
                      showScore={true}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <Filter className="h-16 w-16 text-gray-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-400 mb-2">Selecciona una película</h3>
                <p className="text-gray-500">Haz clic en cualquier película para ver recomendaciones similares</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
