import unittest
import sys
import os

if __name__ == "__main__":
    # 프로젝트 루트에서 실행 시 src 모듈을 찾을 수 있도록 경로 추가
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    
    # tests 폴더 내의 모든 테스트 파일(test_*.py) 자동 검색
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 테스트 실행 (결과 상세 출력)
    print(f"🚀 Running {suite.countTestCases()} tests...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    sys.exit(not result.wasSuccessful())