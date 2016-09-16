for pkg in $(find . -maxdepth 3 -type f -name package.json)
do
	echo $pkg
	cd $(dirname $pkg)
	npm install
	npm run build
done
