"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Star, Calendar, TrendingUp } from "lucide-react"
import { gsap } from "gsap"

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

interface MovieCardProps {
  movie: Movie
  index: number
  onClick?: () => void
  showScore?: boolean
  showRating?: boolean
  showYear?: boolean
}

export default function MovieCard({
  movie,
  index,
  onClick,
  showScore = false,
  showRating = false,
  showYear = false,
}: MovieCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    // Animación de entrada con delay basado en el índice
    gsap.fromTo(
      `.movie-card-${movie.movie_id}`,
      { opacity: 0, y: 30, scale: 0.9 },
      {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.6,
        delay: index * 0.1,
        ease: "back.out(1.7)",
      },
    )
  }, [movie.movie_id, index])

  const handleMouseEnter = () => {
    gsap.to(`.movie-card-${movie.movie_id}`, {
      scale: 1.05,
      y: -10,
      duration: 0.3,
      ease: "power2.out",
    })
  }

  const handleMouseLeave = () => {
    gsap.to(`.movie-card-${movie.movie_id}`, {
      scale: 1,
      y: 0,
      duration: 0.3,
      ease: "power2.out",
    })
  }

  const handleClick = () => {
    if (onClick) {
      // Animación de click
      gsap.to(`.movie-card-${movie.movie_id}`, {
        scale: 0.95,
        duration: 0.1,
        yoyo: true,
        repeat: 1,
        onComplete: onClick,
      })
    }
  }

  return (
    <Card
      className={`movie-card movie-card-${movie.movie_id} bg-white/10 backdrop-blur-sm border-white/20 overflow-hidden transition-all duration-300 ${onClick ? "cursor-pointer hover:border-purple-400/50" : ""}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
    >
      <CardContent className="p-0">
        {/* Poster Image */}
        <div className="relative aspect-[2/3] bg-gradient-to-br from-gray-800 to-gray-900">
          {movie.poster_path && !imageError ? (
            <>
              <img
                src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`}
                alt={movie.title}
                className={`w-full h-full object-cover transition-opacity duration-300 ${imageLoaded ? "opacity-100" : "opacity-0"}`}
                onLoad={() => setImageLoaded(true)}
                onError={() => setImageError(true)}
              />
              {!imageLoaded && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
                </div>
              )}
            </>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-2">🎬</div>
                <div className="text-xs">Sin imagen</div>
              </div>
            </div>
          )}

          {/* Overlay with scores */}
          <div className="absolute top-2 left-2 flex flex-col space-y-1">
            {showScore && movie.score && (
              <Badge className="bg-purple-600/90 text-white text-xs">
                <TrendingUp className="h-3 w-3 mr-1" />
                {(movie.score * 100).toFixed(0)}%
              </Badge>
            )}
            {showRating && movie.vote_average && (
              <Badge className="bg-yellow-600/90 text-white text-xs">
                <Star className="h-3 w-3 mr-1" />
                {movie.vote_average.toFixed(1)}
              </Badge>
            )}
          </div>

          {showYear && movie.year && (
            <Badge className="absolute top-2 right-2 bg-blue-600/90 text-white text-xs">
              <Calendar className="h-3 w-3 mr-1" />
              {movie.year}
            </Badge>
          )}
        </div>

        {/* Movie Info */}
        <div className="p-4">
          <h3 className="font-semibold text-white text-sm leading-tight mb-2 line-clamp-2">{movie.title}</h3>

          {movie.full_genres && (
            <div className="flex flex-wrap gap-1 mb-2">
              {movie.full_genres
                .split("|")
                .slice(0, 2)
                .map((genre, i) => (
                  <Badge key={i} variant="outline" className="border-gray-500 text-gray-300 text-xs px-2 py-0">
                    {genre}
                  </Badge>
                ))}
            </div>
          )}

          {movie.overview && <p className="text-gray-400 text-xs leading-relaxed line-clamp-3">{movie.overview}</p>}
        </div>
      </CardContent>
    </Card>
  )
}
