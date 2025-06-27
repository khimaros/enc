answer.ods: answer.csv
	csv2ods -i "$<" -o "$@"

answer.csv: question.en
	enc "$<" -o "$@"
