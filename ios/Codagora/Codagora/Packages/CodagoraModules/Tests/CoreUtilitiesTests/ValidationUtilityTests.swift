//
//  ValidationUtilityTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

import Testing
@testable import CoreUtilities

struct ValidationUtilityTests {
    @Test("空白以外の氏名を有効と判定する")
    func acceptsValidName() {
        #expect(
            ValidationUtility.isValidName("陽翔")
        )
    }

    @Test("空白だけの氏名を無効と判定する")
    func rejectsWhitespaceOnlyName() {
        #expect(
            !ValidationUtility.isValidName("   ")
        )
    }

    @Test("有効なユーザー名を受け入れる")
    func acceptsValidUsername() {
        #expect(
            ValidationUtility.isValidUsername("haruto-24")
        )
    }

    @Test("使用できない記号を含むユーザー名を拒否する")
    func rejectsInvalidUsernameCharacter() {
        #expect(
            !ValidationUtility.isValidUsername("haruto_24")
        )
    }

    @Test("30文字のユーザー名を受け入れる")
    func acceptsThirtyCharacterUsername() {
        let username = String(repeating: "a", count: 30)

        #expect(
            ValidationUtility.isValidUsername(username)
        )
    }

    @Test("31文字のユーザー名を拒否する")
    func rejectsThirtyOneCharacterUsername() {
        let username = String(repeating: "a", count: 31)

        #expect(
            !ValidationUtility.isValidUsername(username)
        )
    }

    @Test("有効なメールアドレスを受け入れる")
    func acceptsValidEmail() {
        #expect(
            ValidationUtility.isValidEmail(
                "mail@example.com"
            )
        )
    }

    @Test("不正なメールアドレスを拒否する")
    func rejectsInvalidEmail() {
        #expect(
            !ValidationUtility.isValidEmail("mail@")
        )
    }

    @Test("条件を満たすパスワードを受け入れる")
    func acceptsValidPassword() {
        #expect(
            ValidationUtility.isValidPassword("Abcdefg1")
        )
    }

    @Test("大文字を含まないパスワードを拒否する")
    func rejectsPasswordWithoutUppercase() {
        #expect(
            !ValidationUtility.isValidPassword("abcdefg1")
        )
    }

    @Test("小文字を含まないパスワードを拒否する")
    func rejectsPasswordWithoutLowercase() {
        #expect(
            !ValidationUtility.isValidPassword("ABCDEFG1")
        )
    }

    @Test("数字を含まないパスワードを拒否する")
    func rejectsPasswordWithoutNumber() {
        #expect(
            !ValidationUtility.isValidPassword("Abcdefgh")
        )
    }

    @Test("7文字のパスワードを拒否する")
    func rejectsSevenCharacterPassword() {
        #expect(
            !ValidationUtility.isValidPassword("Abcdef1")
        )
    }

    @Test("同じパスワードを一致と判定する")
    func matchingPasswordsReturnTrue() {
        #expect(
            ValidationUtility.passwordsMatch(
                "Abcdefg1",
                "Abcdefg1"
            )
        )
    }

    @Test("異なるパスワードを不一致と判定する")
    func differentPasswordsReturnFalse() {
        #expect(
            !ValidationUtility.passwordsMatch(
                "Abcdefg1",
                "Abcdefg2"
            )
        )
    }

    @Test("確認用パスワードが空の場合は不一致と判定する")
    func emptyConfirmationPasswordReturnsFalse() {
        #expect(
            !ValidationUtility.passwordsMatch(
                "Abcdefg1",
                ""
            )
        )
    }
}
