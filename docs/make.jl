using Documenter

makedocs(
    sitename = "CumulantAnalysis.jl",
    authors = "Ethan Meitz & Alois Castellano",
    format = Documenter.HTML(
        prettyurls = get(ENV, "CI", "false") == "true",
        canonical = "https://ejmeitz.github.io/CumulantAnalysis.jl",
    ),
    pages = [
        "Home" => "index.md",
        "Theory" => "theory.md",
        "Julia" => "julia.md",
        "Python" => "python.md",
    ],
)

deploydocs(
    repo = "github.com/ejmeitz/CumulantAnalysis.jl.git",
    devbranch = "main",
)
