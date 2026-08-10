import type { FatigueAnswers } from '../../types/api'

/** The six check-in questions, in the order they are asked.
 *
 *  These are the exact signals `services/fatigue.py` scores - recovery, performance
 *  trend, joint pain, sleep, motivation, appetite. The wording asks about the last few
 *  sessions rather than today, because one bad day is not fatigue. */
export type FatigueQuestion = {
  key: keyof FatigueAnswers
  question: string
  options: { value: string | boolean; label: string }[]
}

export const FATIGUE_QUESTIONS: FatigueQuestion[] = [
  {
    key: 'recovery_quality',
    question: 'Как се възстановяваш между тренировките?',
    options: [
      { value: 'poor', label: 'Лошо' },
      { value: 'fair', label: 'Средно' },
      { value: 'good', label: 'Добре' },
    ],
  },
  {
    key: 'performance_trend',
    question: 'Как се движи представянето ти в залата?',
    options: [
      { value: 'declining', label: 'Спада' },
      { value: 'stable', label: 'Без промяна' },
      { value: 'improving', label: 'Подобрява се' },
    ],
  },
  {
    key: 'joint_pain',
    question: 'Имаш ли болка в стави или сухожилия?',
    options: [
      { value: true, label: 'Да' },
      { value: false, label: 'Не' },
    ],
  },
  {
    key: 'sleep_quality',
    question: 'Как спиш последната седмица?',
    options: [
      { value: 'poor', label: 'Лошо' },
      { value: 'fair', label: 'Средно' },
      { value: 'good', label: 'Добре' },
    ],
  },
  {
    key: 'motivation',
    question: 'Как е желанието за тренировка?',
    options: [
      { value: 'low', label: 'Ниско' },
      { value: 'moderate', label: 'Умерено' },
      { value: 'high', label: 'Високо' },
    ],
  },
  {
    key: 'appetite',
    question: 'Как е апетитът ти?',
    options: [
      { value: 'decreased', label: 'Намален' },
      { value: 'normal', label: 'Нормален' },
      { value: 'increased', label: 'Повишен' },
    ],
  },
]

export const DECISION_LABEL: Record<string, string> = {
  continue: 'Продължавай по план',
  caution: 'Внимание — намали обема',
  deload: 'Време е за deload',
}
