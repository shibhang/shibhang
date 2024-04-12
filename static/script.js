$(document).ready(function () {
  // Function to toggle sidebar on hamburger icon click
  $(".hamburger").click(function () {
    $(".sidebar").toggleClass("sidebar-open");
  });

  // Function to get user's location
  function getUserLocation() {
    $.get("https://ipapi.co/json/", function (data) {
      var countryCode = data.country;
      var countryName = countryCodeToName(countryCode);
      $("#location").text("Your Location: " + countryName + ", " + data.region);
      fetchTopMovies(countryName.toLowerCase());
    });
  }

  // Function to convert country code to country name
  function countryCodeToName(countryCode) {
    switch (countryCode) {
      case "IN":
        return "India";
      case "NL":
        return "Netherlands";
      case "JP":
        return "Japan";
      case "US":
        return "USA";
      case "PL":
        return "Poland";
      // Add cases for other country codes as needed
      default:
        return countryCode;
    }
  }

  // Function to fetch top movies based on country name
  function fetchTopMovies(countryName) {
    $.ajax({
      url: "/auto_recommendations",
      type: "GET",
      data: {
        location: countryName,
        num_recommendations: 12,
      },
      beforeSend: function () {
        // Show loading spinner or animation
        $("#autoLoading").show();
      },
      success: function (response) {
        var movies = response.automatic_recommendations;
        var moviesList = $("#automaticRecommendationsList");
        moviesList.empty();
        $.each(movies, function (index, movie) {
          var movieElement =
            '<div class="movie">' +
            '<img src="' +
            movie.poster +
            '" alt="' +
            movie.movie_title +
            '" data-youtube-id="' +
            movie.trailer_id +
            '" class="playTrailer">' +
            "<h3>" +
            movie.movie_title +
            "</h3>" +
            "</div>";
          moviesList.append(movieElement);
        });
        attachTrailerClickListener();
      },
      complete: function () {
        $("#autoLoading").hide();
      },
      error: function (xhr, status, error) {
        console.error("Error fetching top movies:", error);
      },
    });
  }

  // Call function to get user's location when the page loads
  getUserLocation();

  // Function to search movies
  function searchMovies() {
    var formData = $("#movieForm").serialize();
    var movieTitle = $("#movieTitle").val();
    if (!movieTitle) {
      // If movie title is empty
      $("#promptMessage").text(
        "Please enter the movie name for the Recommendations !"
      );
      return;
    }
    $("#promptMessage").empty();

    document
      .getElementById("recommendations")
      .scrollIntoView({ behavior: "smooth" });

    $("#movieLoading").show();
    $.ajax({
      type: "POST",
      url: "/recommendations",
      data: formData,
      dataType: "json",
      beforeSend: function () {
        $("#movieLoading").show();
      },
      success: function (response) {
        $("#recommendationsList").empty();
        if (response.recommendations.length > 0) {
          $.each(response.recommendations, function (index, recommendation) {
            var poster = recommendation.poster || "placeholder.jpg";
            var movieTitle = recommendation.movie_title;
            var movieElement =
              '<div class="movie">' +
              '<img src="' +
              poster +
              '" alt="' +
              movieTitle +
              '" data-youtube-id="' +
              recommendation.trailer_id +
              '" class="playTrailer">' +
              "<h3>" +
              movieTitle +
              "</h3>" +
              "</div>";
            $("#recommendationsList").append(movieElement);
          });
          attachTrailerClickListener();
        } else {
          $("#recommendationsList").html("<p>No recommendations found.</p>");
        }
      },
      complete: function () {
        $("#movieLoading").hide();
      },
      error: function (xhr, status, error) {
        console.error("Error:", error);
        $("#recommendationsList").html(
          "<p>Error fetching recommendations. Please try again later.</p>"
        );
      },
    });
  }

  // Call searchMovies function when the form is submitted
  $("#movieForm").on("submit", function (event) {
    event.preventDefault();
    searchMovies();
  });

  // Autocomplete for movie title input
  $("#movieTitle").autocomplete({
    source: function (request, response) {
      $.ajax({
        url: "/autocomplete",
        data: { term: request.term },
        dataType: "json",
        success: function (data) {
          response(data.titles);
        },
        error: function (xhr, status, error) {
          console.error("Error:", error);
          response([]);
        },
      });
    },
    minLength: 2,
  });

  // Function to handle genre filter click event
  $("#genreContent").on("click", ".filter-item", function (e) {
    e.preventDefault();
    var genre = $(this).text();
    getFilteredRecommendations("genre", genre);

    document
      .getElementById("recommendations")
      .scrollIntoView({ behavior: "smooth" });
  });

  // Function to handle country filter click event
  $("#countryContent").on("click", ".filter-item", function (e) {
    e.preventDefault();
    var country = $(this).text();
    getFilteredRecommendations("country", country);

    document
      .getElementById("recommendations")
      .scrollIntoView({ behavior: "smooth" });
  });

  // Function to handle year filter click event
  $("#yearContent").on("click", ".filter-item", function (e) {
    e.preventDefault();
    var year = $(this).text();
    getFilteredRecommendationsByYear(year);

    document
      .getElementById("recommendations")
      .scrollIntoView({ behavior: "smooth" });
  });

  // Function to fetch filtered recommendations
  function getFilteredRecommendations(
    filterType,
    filterValue,
    num_recommendations = 24
  ) {
    $.ajax({
      type: "GET",
      url: "/filtered_recommendations",
      data: { filterType: filterType, filterValue: filterValue },
      dataType: "json",
      beforeSend: function () {
        $("#movieLoading").show();
      },
      success: function (response) {
        var recommendations = response.recommendations;
        updateRecommendations(recommendations);
        attachTrailerClickListener();
      },
      complete: function () {
        $("#movieLoading").hide();
      },
      error: function (xhr, status, error) {
        console.error("Error:", error);
      },
    });
  }

  // Function to fetch filtered recommendations by year
  function getFilteredRecommendationsByYear(year, num_recommendations = 24) {
    $.ajax({
      type: "GET",
      url: "/filtered_recommendations_by_year",
      data: { year: year },
      dataType: "json",
      beforeSend: function () {
        $("#movieLoading").show();
      },
      success: function (response) {
        var recommendations = response.recommendations;
        updateRecommendations(recommendations);
        attachTrailerClickListener();
      },
      complete: function () {
        $("#movieLoading").hide();
      },
      error: function (xhr, status, error) {
        console.error("Error:", error);
      },
    });
  }

  // Function to update recommendations
  function updateRecommendations(recommendations) {
    var recommendationsList = $("#recommendationsList");
    recommendationsList.empty();
    if (recommendations.length > 0) {
      $.each(recommendations, function (index, recommendation) {
        var movieElement =
          '<div class="movie">' +
          '<img src="' +
          recommendation.poster +
          '" alt="' +
          recommendation.movie_title +
          '" data-youtube-id="' +
          recommendation.trailer_id +
          '" class="movie-poster">' +
          "<h3>" +
          recommendation.movie_title +
          "</h3>" +
          "</div>";
        recommendationsList.append(movieElement);
      });
    } else {
      recommendationsList.html("<p>No recommendations found.</p>");
    }
  }

  // Function to handle playing trailer when clicking poster
  function attachTrailerClickListener() {
    $(document).on("click", ".movie img", function () {
      var movieTitle = $(this).closest(".movie").find("h3").text();
      fetchTrailer(movieTitle);
    });
  }

  // Function to fetch movie trailer and poster
  function fetchTrailer(movieTitle) {
    $.ajax({
      type: "POST",
      url: "/fetch_trailer",
      data: { movie_title: movieTitle },
      dataType: "json",
      success: function (response) {
        if (response.movie_details) {
          var trailerId = response.movie_details.trailer_id;
          console.log("Trailer ID:", trailerId);

          // Open a new window with the movie details
          var newWindow = window.open("", "_blank");
          var content =
            "<div class='display-content' style='display: flex; flex-direction: row; justify-content: space-around; align-items: center; text-align: center;'>";

          content += "<div style='flex: 1;'>";
          content +=
            '<iframe class="youtube-video" width="854" height="480" src="https://www.youtube.com/embed/' +
            trailerId +
            '" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>';
          content += "</div>";

          content +=
            "<div class='movie-details' style='display: flex; justify-content: flex-start; align-items: center; width: 100%; margin-top: 20px;'>";

          content += "<div onclick='openTrailer(\"" + trailerId + "\");'>";
          content +=
            "<img class='poster-image' src='" +
            response.movie_details.poster +
            "' style='max-width: 200px; margin-left: 50px; margin-right: 20px; cursor: pointer;'>";
          content += "</div>";

          content +=
            "<div style='flex: 1; display: flex; flex-direction: column; text-align: left;'>";
          content += "<div style='text-align: left;'>";
          content += "<h2 style='margin-top: 20px;'>Movie Details:</h2>";
          content +=
            "<h3 style='color: red;'>" +
            response.movie_details.movie_title +
            "</h3>";
          content +=
            "<p style='text-align: left;'>" +
            response.movie_details.top_cast +
            "</p>";
          content +=
            "<p style='text-align: left;'>" +
            response.movie_details.director +
            "</p>";
          content +=
            "<p style='text-align: left;'>" +
            response.movie_details.country +
            "</p>";
          content +=
            "<p style='text-align: left;'>" +
            response.movie_details.genre +
            "</p>";
          content +=
            "<p style='text-align: left;'>" +
            response.movie_details.runtime +
            "</p>";
          content +=
            "<p style='text-align: left;'>" +
            response.movie_details.imdb_score +
            "</p>";
          content += "</div>";
          content += "</div>";

          content += "</div>";

          $(newWindow.document.head).append(
            "<style>" +
              "@media (max-width: 600px) {" +
              ".youtube-video {" +
              "width: 426px;" +
              "height: 260px;" +
              "}" +
              ".poster-image {" +
              "width: 150px;" +
              "height: auto;" +
              "}" +
              "}" +
              "</style>"
          );

          $(newWindow.document.body).css({
            "font-family": "Arial, sans-serif",
            "background-color": "#1e1e1e",
            color: "#fff",
            padding: "20px",
            "box-sizing": "border-box",
            display: "flex",
            "flex-direction": "column",
            height: "100%",
          });

          $(newWindow.document.body).html(content);
        } else {
          console.log("No movie details available for " + movieTitle);
        }
      },
      error: function (xhr, status, error) {
        console.error("Error fetching movie details:", error);
      },
    });
  }

  // Function to open trailer with the provided trailerId
  function openTrailer(trailerId) {
    console.log("Trailer ID:", trailerId);

    var trailerUrl = "https://www.youtube.com/watch?v=" + trailerId;
    window.open(trailerUrl, "_blank");
  }
});
