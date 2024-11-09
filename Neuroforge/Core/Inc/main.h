/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f3xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define MicroSD_CS_Pin GPIO_PIN_2
#define MicroSD_CS_GPIO_Port GPIOE
#define SDCard_Detect_Pin GPIO_PIN_3
#define SDCard_Detect_GPIO_Port GPIOE
#define SHIELD_Pin GPIO_PIN_4
#define SHIELD_GPIO_Port GPIOE
#define SHIELD_CT_Pin GPIO_PIN_5
#define SHIELD_CT_GPIO_Port GPIOE
#define JOY_SEL_Pin GPIO_PIN_6
#define JOY_SEL_GPIO_Port GPIOE
#define PC14_OSC32_IN_Pin GPIO_PIN_14
#define PC14_OSC32_IN_GPIO_Port GPIOC
#define PC15_OSC32_OUT_Pin GPIO_PIN_15
#define PC15_OSC32_OUT_GPIO_Port GPIOC
#define JOY_RIGHT_Pin GPIO_PIN_9
#define JOY_RIGHT_GPIO_Port GPIOF
#define JOY_UP_Pin GPIO_PIN_10
#define JOY_UP_GPIO_Port GPIOF
#define PF0_OSC_IN_Pin GPIO_PIN_0
#define PF0_OSC_IN_GPIO_Port GPIOF
#define PF1_OSC_OUT_Pin GPIO_PIN_1
#define PF1_OSC_OUT_GPIO_Port GPIOF
#define LED1_Pin GPIO_PIN_0
#define LED1_GPIO_Port GPIOC
#define LED2_Pin GPIO_PIN_1
#define LED2_GPIO_Port GPIOC
#define LED3_Pin GPIO_PIN_2
#define LED3_GPIO_Port GPIOC
#define LED4_Pin GPIO_PIN_3
#define LED4_GPIO_Port GPIOC
#define JOY_DOWN_Pin GPIO_PIN_2
#define JOY_DOWN_GPIO_Port GPIOF
#define LDR_OUT_Pin GPIO_PIN_1
#define LDR_OUT_GPIO_Port GPIOA
#define Key_Button_Pin GPIO_PIN_2
#define Key_Button_GPIO_Port GPIOA
#define COM_IN__Pin GPIO_PIN_3
#define COM_IN__GPIO_Port GPIOA
#define JOY_LEFT_Pin GPIO_PIN_4
#define JOY_LEFT_GPIO_Port GPIOF
#define ADC_DAC_SAR1_Pin GPIO_PIN_4
#define ADC_DAC_SAR1_GPIO_Port GPIOA
#define ADC_DAC_SAR2_Pin GPIO_PIN_5
#define ADC_DAC_SAR2_GPIO_Port GPIOA
#define COMP_OUT_Pin GPIO_PIN_7
#define COMP_OUT_GPIO_Port GPIOA
#define USB_DISCONNECT_Pin GPIO_PIN_5
#define USB_DISCONNECT_GPIO_Port GPIOC
#define MIC_IN_Pin GPIO_PIN_0
#define MIC_IN_GPIO_Port GPIOB
#define ADC_POT_IN_Pin GPIO_PIN_1
#define ADC_POT_IN_GPIO_Port GPIOB
#define V1_8_POR_Pin GPIO_PIN_2
#define V1_8_POR_GPIO_Port GPIOB
#define PRESSURE_P_Pin GPIO_PIN_8
#define PRESSURE_P_GPIO_Port GPIOE
#define PRESSURE_N_Pin GPIO_PIN_9
#define PRESSURE_N_GPIO_Port GPIOE
#define PRESSURE_TEMP_Pin GPIO_PIN_14
#define PRESSURE_TEMP_GPIO_Port GPIOE
#define AUDIO_RST_Pin GPIO_PIN_11
#define AUDIO_RST_GPIO_Port GPIOD
#define SLIDER_1_Pin GPIO_PIN_12
#define SLIDER_1_GPIO_Port GPIOD
#define SLIDER_2_Pin GPIO_PIN_13
#define SLIDER_2_GPIO_Port GPIOD
#define SLIDER_3_Pin GPIO_PIN_14
#define SLIDER_3_GPIO_Port GPIOD
#define SLIDER_CT_Pin GPIO_PIN_15
#define SLIDER_CT_GPIO_Port GPIOD
#define I2S_CMD_Pin GPIO_PIN_6
#define I2S_CMD_GPIO_Port GPIOC
#define I2S_CK_Pin GPIO_PIN_7
#define I2S_CK_GPIO_Port GPIOC
#define I2S_MCLK_Pin GPIO_PIN_8
#define I2S_MCLK_GPIO_Port GPIOC
#define I2S_DIN_Pin GPIO_PIN_9
#define I2S_DIN_GPIO_Port GPIOC
#define I2C2_SMB_Pin GPIO_PIN_8
#define I2C2_SMB_GPIO_Port GPIOA
#define I2C2_SCL_Pin GPIO_PIN_9
#define I2C2_SCL_GPIO_Port GPIOA
#define I2C2_SDA_Pin GPIO_PIN_10
#define I2C2_SDA_GPIO_Port GPIOA
#define TMS_SWDIO_Pin GPIO_PIN_13
#define TMS_SWDIO_GPIO_Port GPIOA
#define TMS_SWCLK_Pin GPIO_PIN_14
#define TMS_SWCLK_GPIO_Port GPIOA
#define TDI_Pin GPIO_PIN_15
#define TDI_GPIO_Port GPIOA
#define SPI3_SCK_Pin GPIO_PIN_10
#define SPI3_SCK_GPIO_Port GPIOC
#define SPI3_MISO_Pin GPIO_PIN_11
#define SPI3_MISO_GPIO_Port GPIOC
#define SPI3_MOSI_Pin GPIO_PIN_12
#define SPI3_MOSI_GPIO_Port GPIOC
#define CAN_RX_Pin GPIO_PIN_0
#define CAN_RX_GPIO_Port GPIOD
#define CAN_TX_Pin GPIO_PIN_1
#define CAN_TX_GPIO_Port GPIOD
#define LCD_CS_Pin GPIO_PIN_2
#define LCD_CS_GPIO_Port GPIOD
#define USART2_CTS_Pin GPIO_PIN_3
#define USART2_CTS_GPIO_Port GPIOD
#define USART2_RTS_Pin GPIO_PIN_4
#define USART2_RTS_GPIO_Port GPIOD
#define USART2_TX_Pin GPIO_PIN_5
#define USART2_TX_GPIO_Port GPIOD
#define USART2_RX_Pin GPIO_PIN_6
#define USART2_RX_GPIO_Port GPIOD
#define HDMI_HPD_SOURCE_Pin GPIO_PIN_7
#define HDMI_HPD_SOURCE_GPIO_Port GPIOD
#define TDO_SWO_Pin GPIO_PIN_3
#define TDO_SWO_GPIO_Port GPIOB
#define TRST_Pin GPIO_PIN_4
#define TRST_GPIO_Port GPIOB
#define IR_IN_Pin GPIO_PIN_5
#define IR_IN_GPIO_Port GPIOB
#define I2C1_SCL_Pin GPIO_PIN_6
#define I2C1_SCL_GPIO_Port GPIOB
#define I2C1_SDA_Pin GPIO_PIN_7
#define I2C1_SDA_GPIO_Port GPIOB
#define HDMI_CEC_Pin GPIO_PIN_8
#define HDMI_CEC_GPIO_Port GPIOB
#define IR_LED_Pin GPIO_PIN_9
#define IR_LED_GPIO_Port GPIOB
#define HDMI_HPD_SINK_Pin GPIO_PIN_0
#define HDMI_HPD_SINK_GPIO_Port GPIOE

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
