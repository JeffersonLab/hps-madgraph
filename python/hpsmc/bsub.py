from batch import LSF

if __name__ == "__main__":
    submit = LSF()
    submit.parse_args()
    submit.submit_all()
