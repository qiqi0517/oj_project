from app.judge.comparator import compare_output
from app.judge.runner import run_language_case
from app.models.enums import JudgeResult
from app.models.judge import JudgeCaseResult, JudgeResultData, ProcessRunResult
from app.models.language import LanguagePublic
from app.models.problem import TestCase


def build_case_result(
    case_id: int,
    result: JudgeResult,
    run_result: ProcessRunResult,
) -> JudgeCaseResult:
    return JudgeCaseResult(
        id=case_id,
        result=result,  # type: ignore
        score=10 if result == JudgeResult.AC else 0,
        time=run_result.time_used,
        memory=run_result.memory_used,
        exit_code=run_result.exit_code,
        stdout=run_result.stdout,
        stderr=run_result.stderr,
        compile_info=run_result.compile_info,
    )


async def evaluate_case(
    source_code: str,
    test_case: TestCase,
    case_id: int,
    time_limit: float,
    memory_limit: int,
    language: LanguagePublic | None = None,
) -> JudgeCaseResult:
    if language is None:
        language = LanguagePublic(
            name="python",
            file_ext=".py",
            compile_cmd=None,
            run_cmd="python3 {src}",
            time_limit=time_limit,
            memory_limit=memory_limit,
        )
    run_result = await run_language_case(
        source_code=source_code,
        input_data=test_case.input,
        time_limit=time_limit,
        memory_limit=memory_limit,
        language=language,
    )
    if run_result.system_error is not None:
        return build_case_result(case_id, JudgeResult.UNK, run_result)
    if run_result.timed_out:
        return build_case_result(case_id, JudgeResult.TLE, run_result)
    if run_result.memory_exceeded:
        return build_case_result(case_id, JudgeResult.MLE, run_result)
    if run_result.compile_error:
        return build_case_result(case_id, JudgeResult.CE, run_result)
    if run_result.decode_error or run_result.exit_code != 0:
        return build_case_result(case_id, JudgeResult.RE, run_result)
    if compare_output(run_result.stdout, test_case.output):
        return build_case_result(case_id, JudgeResult.AC, run_result)
    return build_case_result(case_id, JudgeResult.WA, run_result)


def final_result(cases: list[JudgeCaseResult]) -> JudgeResult:
    priorities = (
        JudgeResult.UNK,
        JudgeResult.CE,
        JudgeResult.MLE,
        JudgeResult.TLE,
        JudgeResult.RE,
        JudgeResult.WA,
    )
    for result in priorities:
        if any(case.result == result for case in cases):
            return result
    return JudgeResult.AC


async def evaluate_language(
    source_code: str,
    testcases: list[TestCase],
    time_limit: float,
    memory_limit: int,
    language: LanguagePublic,
) -> JudgeResultData:
    cases = [
        await evaluate_case(
            source_code,
            testcase,
            index,
            time_limit,
            memory_limit,
            language,
        )
        for index, testcase in enumerate(testcases, start=1)
    ]
    result = final_result(cases)
    return JudgeResultData(
        result=result,
        score=sum(case.score for case in cases),
        counts=len(cases) * 10,
        total_time=sum(case.time for case in cases),
        cases=cases,
        compile_info=next(
            (case.compile_info for case in cases if case.compile_info),
            None,
        ),
        error_info=("judge system error" if result == JudgeResult.UNK else None),
    )
