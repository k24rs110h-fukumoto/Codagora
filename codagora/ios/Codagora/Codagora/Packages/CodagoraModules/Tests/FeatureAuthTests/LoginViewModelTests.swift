//
//  LoginViewModelTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Testing
import CoreNetworking
@testable import FeatureAuth

struct LoginViewModelTests {
    @Test("有効な入力ではログイン可能になる")
    @MainActor
    func enablesSubmitForValidInput() {
        let viewModel = LoginViewModel(
            loginUseCase: MockLoginUseCase(
                result: .success(Self.user)
            )
        )
        
        viewModel.email = "mail@example.com"
        viewModel.password = "Password1"
        
        #expect(viewModel.canSubmit)
    }
    
    @Test("不正なメールアドレスではログインできない")
    @MainActor
    func disablesSubmitForInvalidEmail() {
        let viewModel = LoginViewModel(
            loginUseCase: MockLoginUseCase(
                result: .success(Self.user)
            )
        )
        
        viewModel.email = "invalid-email"
        viewModel.password = "Password1"
        
        #expect(!viewModel.canSubmit)
    }
    
    @Test("パスワードが空の場合はログインできない")
    @MainActor
    func disablesSubmitForEmptyPassword() {
        let viewModel = LoginViewModel(
            loginUseCase: MockLoginUseCase(
                result: .success(Self.user)
            )
        )
        
        viewModel.email = "mail@example.com"
        viewModel.password = ""
        
        #expect(!viewModel.canSubmit)
    }
    
    @Test("ログイン成功時に認証済みユーザーを返す")
    @MainActor
    func returnsAuthenticatedUser() async {
        let useCase = MockLoginUseCase(
            result: .success(Self.user)
        )
        
        let viewModel = LoginViewModel(
            loginUseCase: useCase
        )
        
        viewModel.email = "mail@example.com"
        viewModel.password = "Password1"
        
        let result = await viewModel.login()
        
        #expect(result == Self.user)
        #expect(viewModel.errorMessage == nil)
        #expect(!viewModel.isLoading)
    }
    
    @Test("メールアドレス前後の空白を削除してUseCaseへ渡す")
    @MainActor
    func trimsEmailBeforeLogin() async {
        let useCase = MockLoginUseCase(
            result: .success(Self.user)
        )
        
        let viewModel = LoginViewModel(
            loginUseCase: useCase
        )
        
        viewModel.email = "  mail@example.com  "
        viewModel.password = "Password1"
        
        _ = await viewModel.login()
        
        let credentials =
        await useCase.receivedCredentials
        
        #expect(
            credentials?.email == "mail@example.com"
        )
        
        #expect(
            credentials?.password == "Password1"
        )
    }
    
    @Test("ログイン失敗時に画面用エラーメッセージを設定する")
    @MainActor
    func setsErrorMessageWhenLoginFails() async {
        let useCase = MockLoginUseCase(
            result: .failure(
                .unauthorized(nil)
            )
        )
        
        let viewModel = LoginViewModel(
            loginUseCase: useCase
        )
        
        viewModel.email = "mail@example.com"
        viewModel.password = "WrongPassword"
        
        let result = await viewModel.login()
        
        #expect(result == nil)
        
        #expect(
            viewModel.errorMessage ==
            "メールアドレスまたはパスワードが正しくありません。"
        )
        
        #expect(!viewModel.isLoading)
    }
    
    @Test("通信中のログイン二重送信を防止する")
    @MainActor
    func preventsDuplicateLoginRequests() async {
        let useCase = SuspendedLoginUseCase()
        
        let viewModel = LoginViewModel(
            loginUseCase: useCase
        )
        
        viewModel.email = "mail@example.com"
        viewModel.password = "Password1"
        
        let firstTask = Task {
            await viewModel.login()
        }
        
        while await useCase.callCount == 0 {
            await Task.yield()
        }
        
        #expect(viewModel.isLoading)
        
        let secondResult = await viewModel.login()
        
        #expect(secondResult == nil)
        #expect(await useCase.callCount == 1)
        
        await useCase.complete(
            with: Self.user
        )
        
        let firstResult = await firstTask.value
        
        #expect(firstResult == Self.user)
        #expect(!viewModel.isLoading)
    }
    
    private static let user = AuthenticatedUser(
        id: "user-001",
        email: "mail@example.com",
        displayName: "福本 陽翔",
        firstName: "陽翔",
        lastName: "福本",
        avatarUrl: "",
        timezone: "Asia/Tokyo"
    )
}

private actor MockLoginUseCase:
    LoginUseCaseProtocol
{
    enum Result: Sendable {
        case success(AuthenticatedUser)
        case failure(NetworkError)
    }
    
    private let result: Result
    
    private(set) var receivedCredentials:
    LoginCredentials?
    
    init(result: Result) {
        self.result = result
    }
    
    func execute(
        credentials: LoginCredentials
    ) async throws -> AuthenticatedUser {
        receivedCredentials = credentials
        
        switch result {
        case let .success(user):
            return user
            
        case let .failure(error):
            throw error
        }
    }
}

private actor SuspendedLoginUseCase:
    LoginUseCaseProtocol
{
    private var continuation:
    CheckedContinuation<
        AuthenticatedUser,
        any Error
    >?
    
    private(set) var callCount = 0
    
    func execute(
        credentials: LoginCredentials
    ) async throws -> AuthenticatedUser {
        callCount += 1
        
        return try await withCheckedThrowingContinuation {
            continuation = $0
        }
    }
    
    func complete(
        with user: AuthenticatedUser
    ) {
        continuation?.resume(
            returning: user
        )
        
        continuation = nil
    }
}
