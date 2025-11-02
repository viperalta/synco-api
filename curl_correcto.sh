#!/bin/bash

# Para obtener todas las deudas (sin filtro de período)
curl 'http://localhost:8000/admin/debts' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGYzZmVlN2M3YzVlNTY0MTQ2ZWVmNGQiLCJlbWFpbCI6InZpcGVyYWx0YUBnbWFpbC5jb20iLCJleHAiOjE3NjE2ODgxMjMsInR5cGUiOiJhY2Nlc3MifQ.nIWnz3kpB1EFJijAHiP7kUjWfmJ4YrUwhrEJsZPAEKc'

# Para obtener una deuda específica por período
curl 'http://localhost:8000/admin/debts/202510' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGYzZmVlN2M3YzVlNTY0MTQ2ZWVmNGQiLCJlbWFpbCI6InZpcGVyYWx0YUBnbWFpbC5jb20iLCJleHAiOjE3NjE2ODgxMjMsInR5cGUiOiJhY2Nlc3MifQ.nIWnz3kpB1EFJijAHiP7kUjWfmJ4YrUwhrEJsZPAEKc'

