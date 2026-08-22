#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using i64 = long long;

static int imod(i64 x, int p) {
    x %= p;
    if (x < 0) x += p;
    return static_cast<int>(x);
}

static int ipow_int(int a, int n) {
    int r = 1;
    while (n-- > 0) r *= a;
    return r;
}

static bool polynomial_divides(const std::vector<int>& f, const std::vector<int>& g, int p) {
    std::vector<int> rem = f;
    const int nf = static_cast<int>(f.size()) - 1;
    const int ng = static_cast<int>(g.size()) - 1;
    for (int k = nf; k >= ng; --k) {
        const int c = rem[k];
        if (c == 0) continue;
        for (int j = 0; j <= ng; ++j) {
            rem[k - ng + j] = imod(rem[k - ng + j] - 1LL * c * g[j], p);
        }
    }
    for (int i = 0; i < ng; ++i) if (rem[i] != 0) return false;
    return true;
}

static std::vector<int> find_irreducible_polynomial(int p, int n) {
    if (n == 1) return {0, 1};
    const int candidates = ipow_int(p, n);
    for (int code = 0; code < candidates; ++code) {
        std::vector<int> f(n + 1, 0);
        int x = code;
        for (int i = 0; i < n; ++i) { f[i] = x % p; x /= p; }
        f[n] = 1;
        if (f[0] == 0) continue;
        bool reducible = false;
        for (int d = 1; d <= n / 2 && !reducible; ++d) {
            const int divisor_codes = ipow_int(p, d);
            for (int gc = 0; gc < divisor_codes; ++gc) {
                std::vector<int> g(d + 1, 0);
                int y = gc;
                for (int i = 0; i < d; ++i) { g[i] = y % p; y /= p; }
                g[d] = 1;
                if (g[0] == 0) continue;
                if (polynomial_divides(f, g, p)) { reducible = true; break; }
            }
        }
        if (!reducible) return f;
    }
    throw std::runtime_error("failed to find irreducible polynomial");
}

class FiniteField {
public:
    int p, n, q;
    std::vector<int> modulus, square, add_table, add_one;
    std::vector<int8_t> chi;

    FiniteField(int prime, int degree)
        : p(prime), n(degree), q(ipow_int(prime, degree)),
          modulus(find_irreducible_polynomial(prime, degree)) {
        square.resize(q);
        chi.assign(q, -1);
        add_one.resize(q);
        for (int a = 0; a < q; ++a) square[a] = mul(a, a);
        chi[0] = 0;
        for (int a = 1; a < q; ++a) chi[square[a]] = 1;
        add_table.resize(static_cast<size_t>(q) * static_cast<size_t>(q));
        for (int a = 0; a < q; ++a)
            for (int b = 0; b < q; ++b)
                add_table[static_cast<size_t>(a) * q + b] = add_slow(a, b);
        const int one = constant(1);
        for (int a = 0; a < q; ++a) add_one[a] = add(a, one);
    }

    int constant(int k) const { return imod(k, p); }
    int add(int a, int b) const { return add_table[static_cast<size_t>(a) * q + b]; }
    int sub(int a, int b) const { return add_slow(a, neg(b)); }

    int neg(int a) const {
        if (n == 1) return a == 0 ? 0 : p - a;
        int out = 0, place = 1;
        for (int i = 0; i < n; ++i) {
            const int digit = a % p; a /= p;
            out += imod(-digit, p) * place; place *= p;
        }
        return out;
    }

    int scalar(int a, int k) const {
        k = imod(k, p);
        if (n == 1) return static_cast<int>(1LL * a * k % p);
        int out = 0, place = 1;
        for (int i = 0; i < n; ++i) {
            const int digit = a % p; a /= p;
            out += static_cast<int>(1LL * digit * k % p) * place; place *= p;
        }
        return out;
    }

    int mul(int a, int b) const {
        if (n == 1) return static_cast<int>(1LL * a * b % p);
        std::vector<int> av(n), bv(n);
        int aa = a, bb = b;
        for (int i = 0; i < n; ++i) {
            av[i] = aa % p; bv[i] = bb % p; aa /= p; bb /= p;
        }
        std::vector<int> tmp(2 * n - 1, 0);
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j)
                tmp[i + j] = imod(tmp[i + j] + 1LL * av[i] * bv[j], p);
        for (int k = 2 * n - 2; k >= n; --k) {
            const int c = tmp[k];
            if (c == 0) continue;
            for (int i = 0; i < n; ++i)
                tmp[k - n + i] = imod(tmp[k - n + i] - 1LL * c * modulus[i], p);
        }
        int out = 0, place = 1;
        for (int i = 0; i < n; ++i) { out += tmp[i] * place; place *= p; }
        return out;
    }

    std::string modulus_string() const {
        if (n == 1) return "x";
        std::ostringstream out;
        out << "x^" << n;
        for (int i = n - 1; i >= 0; --i) {
            const int c = modulus[i];
            if (c == 0) continue;
            out << "+" << c;
            if (i >= 1) out << "*x";
            if (i >= 2) out << "^" << i;
        }
        return out.str();
    }

private:
    int add_slow(int a, int b) const {
        if (n == 1) return (a + b) % p;
        int out = 0, place = 1;
        for (int i = 0; i < n; ++i) {
            const int digit = (a % p + b % p) % p;
            a /= p; b /= p; out += digit * place; place *= p;
        }
        return out;
    }
};

struct Row {
    int p=0,n=0,q=0,e=0,h=0;
    std::string polynomial;
    i64 t4=0,t8=0,euler=0,full=0,euler_predicted=0,full_predicted=0;
    std::array<i64,16> sums{},predicted{};
};

static Row compute_case(int p, int n) {
    FiniteField F(p,n);
    Row r; r.p=p; r.n=n; r.q=F.q; r.polynomial=F.modulus_string();
    r.e=F.chi[F.constant(-1)]; r.h=F.chi[F.constant(2)];
    i64 s4=0,s8=0;
    for(int x=0;x<F.q;++x){
        int x2=F.square[x],x3=F.mul(x2,x);
        s4+=F.chi[F.sub(x3,x)];
        s8+=F.chi[F.add(F.sub(x3,F.scalar(x2,4)),F.scalar(x,2))];
    }
    r.t4=-s4; r.t8=-s8;
    int one=F.constant(1);
    for(int b=0;b<F.q;++b){
        int bb=F.square[b],q0=F.add_one[bb];
        for(int c=0;c<F.q;++c){
            int cc=F.square[c],q1=F.add_one[cc],q2=F.add(bb,cc),q3=F.add(one,q2);
            int a=F.chi[q0],d=F.chi[q1],f=F.chi[q2],g=F.chi[q3];
            r.sums[0]++; r.sums[1]+=a; r.sums[2]+=d; r.sums[3]+=a*d;
            r.sums[4]+=f; r.sums[5]+=a*f; r.sums[6]+=d*f; r.sums[7]+=a*d*f;
            r.sums[8]+=g; r.sums[9]+=a*g; r.sums[10]+=d*g; r.sums[11]+=a*d*g;
            r.sums[12]+=f*g; r.sums[13]+=a*f*g; r.sums[14]+=d*f*g; r.sums[15]+=a*d*f*g;
            bool E=a>=0&&d>=0&&f>=0; bool P=E&&g>=0; r.euler+=E; r.full+=P;
        }
    }
    i64 q=r.q,e=r.e,h=r.h,t4s=r.t4*r.t4,t8s=r.t8*r.t8;
    r.predicted[0]=q*q; r.predicted[1]=r.predicted[2]=-q; r.predicted[3]=1;
    r.predicted[4]=0; r.predicted[5]=r.predicted[6]=q+1;
    r.predicted[7]=2*h*q+2+e*t8s; r.predicted[8]=e*q;
    r.predicted[9]=r.predicted[10]=1; r.predicted[11]=-e*q+2+t4s;
    r.predicted[12]=-q+e; r.predicted[13]=r.predicted[14]=(1+e)*(-q+1)+t4s;
    r.predicted[15]=-(1+2*e*h)*q+(2+e)+3*t8s;
    i64 Epure=q*q+2*h*q+5+e*t8s;
    i64 Ecorr=2*(1-e)+(1+e)*(3*q-5+6*h-3*r.t4);
    r.euler_predicted=(Epure+Ecorr)/8;
    i64 Fpure=q*q+(2*h-4-2*e-2*e*h)*q+13+4*e+3*t4s+(3+e)*t8s;
    i64 Fcorr=4*(1-e)+(1+e)*(10*q-22+12*h-6*r.t4);
    r.full_predicted=(Fpure+Fcorr)/16;
    return r;
}

int main(int argc,char**argv){
    if(argc!=2){std::cerr<<"usage: finite_field_motive OUTPUT.csv\n";return 2;}
    std::vector<std::pair<int,int>> cases={
        {3,1},{3,2},{3,3},{3,4},{3,5},{3,6},{5,1},{5,2},{5,3},{5,4},
        {7,1},{7,2},{7,3},{7,4},{11,1},{11,2},{11,3},{13,1},{13,2},{13,3},
        {17,1},{17,2},{19,1},{19,2},{23,1},{23,2},{29,1},{29,2},{31,1},{31,2},{37,1},{37,2}
    };
    std::ofstream out(argv[1]);
    out<<"p,n,q,polynomial,e,h,t4,t8,euler,full,euler_predicted,full_predicted";
    for(int i=0;i<16;++i)out<<",S"<<i; for(int i=0;i<16;++i)out<<",P"<<i;
    out<<",all_character_sums_ok,euler_formula_ok,full_formula_ok\n";
    for(auto [p,n]:cases){
        Row r=compute_case(p,n); bool ok=true; for(int i=0;i<16;++i)ok&=r.sums[i]==r.predicted[i];
        bool eok=r.euler==r.euler_predicted,fok=r.full==r.full_predicted;
        out<<r.p<<','<<r.n<<','<<r.q<<",\""<<r.polynomial<<"\","<<r.e<<','<<r.h<<','<<r.t4<<','<<r.t8<<','<<r.euler<<','<<r.full<<','<<r.euler_predicted<<','<<r.full_predicted;
        for(auto x:r.sums)out<<','<<x; for(auto x:r.predicted)out<<','<<x;
        out<<','<<(ok?1:0)<<','<<(eok?1:0)<<','<<(fok?1:0)<<'\n';
        std::cerr<<"p="<<p<<" n="<<n<<" q="<<r.q<<" sums="<<ok<<" E="<<eok<<" F="<<fok<<'\n';
        if(!ok||!eok||!fok)return 1;
    }
    return 0;
}
