pkgname=pokemon-colorscripts-enhanced-git
_pkgname=pokemon-colorscripts
pkgver=r5.9078b1a
pkgrel=1
pkgdesc="CLI utility that prints unicode sprites of pokemon to the terminal"
arch=('any')
url="https://github.com/lelnofake/pokemon-colorscripts-enhanced"
license=('MIT')
depends=('python')
makedepends=('git')
source=("$pkgname::git+$url#branch=main")
md5sums=('SKIP')

pkgver() {
    cd "$pkgname"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
    cd "$pkgname"
    # Creating necessary directories and copying files
    install -Dm644 colorscripts/small/regular/* -t "$pkgdir/usr/share/$_pkgname/colorscripts/small/regular"
    install -Dm644 colorscripts/small/shiny/* -t "$pkgdir/usr/share/$_pkgname/colorscripts/small/shiny"
    install -Dm644 colorscripts/large/regular/* -t "$pkgdir/usr/share/$_pkgname/colorscripts/large/regular"
    install -Dm644 colorscripts/large/shiny/* -t "$pkgdir/usr/share/$_pkgname/colorscripts/large/shiny"
    install -Dm644 pokemon.json "$pkgdir/usr/share/$_pkgname/pokemon.json"
    install -Dm755 pokemon-colorscripts.py "$pkgdir/usr/share/$_pkgname/pokemon-colorscripts.py"
    install -Dm644 LICENSE.txt "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
    install -Dm644 pokemon-colorscripts.1 "$pkgdir/usr/share/man/man1/pokemon-colorscripts.1"
    # creating symlink in usr/bin
    install -d "$pkgdir/usr/bin"
    ln -s "/usr/share/$_pkgname/pokemon-colorscripts.py" "$pkgdir/usr/bin/pokemon-colorscripts"
}
