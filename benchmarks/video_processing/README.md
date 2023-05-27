This benchmark is taken from [https://github.com/spcl/serverless-benchmarks](https://github.com/spcl/serverless-benchmarks).
After installing their tool, you can deploy the video-processing function by running this command:

```bash
./sebs.py benchmark invoke 220.video_processing test --config config/example.json --deployment aws
```