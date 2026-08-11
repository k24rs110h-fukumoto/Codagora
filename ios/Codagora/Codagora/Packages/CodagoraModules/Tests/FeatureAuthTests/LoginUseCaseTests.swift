//
//  LoginUseCaseTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Testing
@testable import FeatureAuth

struct LoginUseCaseTests {
    @Test("ログイン情報をRepositoryへ渡してユーザーを返す")
    func returnsAuthenticatedUser() async throws {
        let expectedUser = AuthenticatedUser(
            id: "user-001",
            email: "mail@example.com",
            displayName: "福本 陽翔",
            firstName: "陽翔",
            lastName: "福本",
            avatarUrl: "",
            timezone: "Asia/Tokyo"
        )

        let repository = MockAuthRepository(
            result: .success(expectedUser)
        )

        let useCase = LoginUseCase(
            repository: repository
        )

        let credentials = LoginCredentials(
            email: "mail@example.com",
            password: "Password1"
        )

        let user = try await useCase.execute(
            credentials: credentials
        )

        let receivedCredentials =
            await repository.receivedCredentials

        #expect(user == expectedUser)
        #expect(receivedCredentials == credentials)
    }

    @Test("Repositoryのエラーを呼び出し元へ返す")
    func propagatesRepositoryError() async {
        let repository = MockAuthRepository(
            result: .failure(.loginFailed)
        )

        let useCase = LoginUseCase(
            repository: repository
        )

        let credentials = LoginCredentials(
            email: "mail@example.com",
            password: "Password1"
        )

        do {
            _ = try await useCase.execute(
                credentials: credentials
            )

            Issue.record(
                "ログインエラーになるはずの処理が成功しました"
            )
        } catch let error as TestError {
            #expect(error == .loginFailed)
        } catch {
            Issue.record(
                "想定外のエラーが発生しました: \(error)"
            )
        }
    }
}

private actor MockAuthRepository: AuthRepository {
    enum Result: Sendable {
        case success(AuthenticatedUser)
        case failure(TestError)
    }

    private let result: Result
    private(set) var receivedCredentials:
        LoginCredentials?

    init(result: Result) {
        self.result = result
    }

    func login(
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
    
    func currentUser() async throws -> AuthenticatedUser {
        switch result {
        case let .success(user):
            return user

        case let .failure(error):
            throw error
        }
    }
    
    func logout() async throws {
        
    }
}

private enum TestError:
    Error,
    Equatable,
    Sendable
{
    case loginFailed
}
