all: both int-only parse-only

both:
	php test.php --parse-script=apps/parse.php --int-script=apps/interpret.py --directory=tests/both --recursive > test-both.html

int-only:
	php test.php --int-script=apps/interpret.py --directory=tests/int-only --recursive --int-only > test-int.html

parse-only:
	php test.php --parse-script=apps/parse.php --directory=tests/parse-only/ --recursive --parse-only > test-parse.html

error:
	php test.php --parse-only --int-only --recursive

