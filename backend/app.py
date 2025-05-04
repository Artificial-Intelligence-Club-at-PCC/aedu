# backend/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# import your existing solver
from math_solver     import solve_math_problem  

app = FastAPI()

# Allow your frontend at localhost:5500 (Live Server) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class SolveRequest(BaseModel):
    problem: str

class SolveResponse(BaseModel):
    solution: str

@app.post("/api/solve", response_model=SolveResponse)
def solve_endpoint(req: SolveRequest):
    sol = solve_math_problem(req.problem)
    if sol is None:
        raise HTTPException(500, "Solver failed – check logs for details.")
    return SolveResponse(solution=sol)
