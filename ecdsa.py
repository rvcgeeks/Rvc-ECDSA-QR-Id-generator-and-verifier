#
# An elliptic curve digital signature algorithm id generator
# in pure python compatable for beaglebone and raspberry pi.
# ideal for databaseless client authorisation using RFID on Rpi
# Works with ANY version of python including v2 and v3 obviously 
# without any library support apart from sys and random which are
# in stdlib of any python.
#
# created by rvcgeeks <github.com/rvcgeeks> (rvchavadekar@gmail.com) @ Pune, India.
#
# secp256k1 curve tuple parameters :: the Bitcoin curve .. plz refer https://www.secg.org/sec2-v2.pdf section 2.4.1

class ecTuple:
  def __init__(self, p, a, b, G, n, h):
    self.p = p; self.a = a; self.b = b; self.G = G; self.n = n; self.h = h
    
C = ecTuple(
  p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f,  # Field characteristic.
  a = 0, b = 7,                                                            # Curve coefficients. looks like y^2 = x^3 + 7
  G = (0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798, # Base point.
       0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8),
  n = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141,  # Subgroup order.
  h = 1                                                                    # Subgroup cofactor.
)
# Modular arithmetic

def imod(k, p): # Returns the inverse of k modulo p. Extended Euclidean algorithm. This function returns the only integer x such that (x * k) % p == 1.
  if k < 0: # k ** -1 = p - (-k) ** -1  (mod p)
    return p - imod(-k, p)
  s, s0 = 0, 1
  t, t0 = 1, 0
  r, r0 = p, k
  while r != 0:
    q = r0 // r
    r0, r = r, r0 - q * r
    s0, s = s, s0 - q * s
    t0, t = t, t0 - q * t
  gcd, x, y = r0, s0, t0
  return x % p

# Functions that work on curve points 

def neg(p): # Returns -p.
  if p is None: # -0 = 0
    return None
  x, y = p
  return (x, -y % C.p)

def add(p1, p2): # Returns the result of p1 + p2 according to the group law.
  if p1 is None: # 0 + p2 = p2
    return p2
  if p2 is None: # p1 + 0 = p1
    return p1
  x1, y1 = p1
  x2, y2 = p2
  if x1 == x2 and y1 != y2: # p1 + (-p1) = 0
    return None
  if x1 == x2: # This is the case p1 == p2.
    m = (3 * x1 * x1 + C.a) * imod(2 * y1, C.p)
  else: # This is the case p1 != p2.
    m = (y1 - y2) * imod(x1 - x2, C.p)
  x3 = m * m - x1 - x2
  y3 = y1 + m * (x3 - x1)
  return (x3 % C.p, -y3 % C.p)

def mul(k, p):  # Returns k * point computed using the double and add algorithm.
  if k % C.n == 0 or p is None:
    return None
  if k < 0: # k * point = -k * (-point)
    return mul(-k, neg(p))
  res = None
  ad = p
  while k:
    if k & 1: # Add.
      res = add(res, ad)
    ad = add(ad, ad) # Double.
    k >>= 1
  return res

# Keypair generation and ECDSA 

from random import randrange

def keygen():  # Generates a random private-public key pair.
  prvk = randrange(1, C.n)
  pubk = mul(prvk, C.G)
  return prvk, pubk
  
def sign(prvk, z):
  r = 0; s = 0
  while not r or not s:
    k = randrange(1, C.n)
    x, y = mul(k, C.G)
    r = x % C.n
    s = ((z + r * prvk) * imod(k, C.n)) % C.n
  return (r, s)
  
def verify(pubk, z, sgn):
  r, s = sgn
  w = imod(s, C.n)
  u1 = (z * w) % C.n
  u2 = (r * w) % C.n
  x, y = add(mul(u1, C.G), mul(u2, pubk))
  return (r % C.n) == (x % C.n)

# Base58 encoding to store keys in compressed manner using safe characters

charset = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
radix = 58 # len(charset)

def itob58(x): # Returns x in a base58 string
  s = ''
  while x >= radix:  
    s = charset[x % radix] + s
    x //= radix
  if (x): s = charset[x] + s
  return s

def b58toi(s): # Decodes the base58 string into an integer
  x = 0; m = 1; s = s[::-1]
  for c in s:
    x += m * charset.index(c)
    m *= radix
  return x

