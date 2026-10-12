This is my first Data Engineer project

what I learned here are:

# Request vs Httpx
- Request can stall the program if there are hundreds of API calls, at that time, I might want to switch to httpx as it supports Async calls
- Build for current requirements, I shouldnt tie myself to a chair and implement a program that handles thousands of API calls when it initially only need 1 to 2 calls once a while